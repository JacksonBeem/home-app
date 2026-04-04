from models.item import Item
from models.item_lookup import ItemLookup
from models.quantity import Quantity
from models.storage_categories import StorageCategory
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from database import engine
from datetime import datetime
from decimal import Decimal, InvalidOperation
import json
from urllib.request import urlopen
from urllib.parse import urlencode

Session = sessionmaker(bind=engine)
session = Session()
_item_tracking_ready = False
_item_lookup_optional_ready = False
_item_lookup_qty_is_numeric = None


# --- Internal helpers ---

def _barcode_candidates(barcode):
    raw = str(barcode).strip()
    if not raw:
        return []

    candidates = [raw]
    if raw.isdigit():
        stripped = raw.lstrip("0")
        if stripped and stripped not in candidates:
            candidates.append(stripped)
        as_int_str = str(int(raw))
        if as_int_str not in candidates:
            candidates.append(as_int_str)
    return candidates


def _get_item_lookup_by_barcode(barcode):
    candidates = _barcode_candidates(barcode)
    for candidate in candidates:
        item_lookup = (
            session.query(ItemLookup)
            .where(text("CAST(barcode AS TEXT) = :barcode"))
            .params(barcode=candidate)
            .first()
        )
        if item_lookup:
            return item_lookup
    return None


def _ensure_item_tracking_columns():
    """
    Ensure optional pantry columns exist on item:
      - storage_categories_id for location assignment/filtering
      - last_scanned for age display
    """
    global _item_tracking_ready
    if _item_tracking_ready:
        return

    # Runtime DDL can destabilize some DB environments; skip automatic ALTERs.
    _item_tracking_ready = True


def _ensure_item_lookup_optional_columns():
    """
    Ensure optional item_lookup columns exist for manual-entry metadata.
    """
    global _item_lookup_optional_ready
    if _item_lookup_optional_ready:
        return

    # Runtime DDL can destabilize some DB environments; skip automatic ALTERs.
    _item_lookup_optional_ready = True


def _to_decimal_or_none(value):
    if value is None:
        return None
    if isinstance(value, (int, float, Decimal)):
        return value

    as_text = str(value).strip()
    if not as_text:
        return None

    try:
        return Decimal(as_text)
    except (InvalidOperation, ValueError):
        return None


def _is_item_lookup_quantity_numeric():
    global _item_lookup_qty_is_numeric
    if _item_lookup_qty_is_numeric is not None:
        return _item_lookup_qty_is_numeric

    try:
        with engine.begin() as conn:
            dtype = conn.execute(
                text(
                    """
                    SELECT data_type
                    FROM information_schema.columns
                    WHERE table_name = 'item_lookup' AND column_name = 'quantity'
                    """
                )
            ).scalar_one_or_none()
        _item_lookup_qty_is_numeric = dtype in ("real", "double precision", "numeric", "integer", "bigint", "smallint")
    except SQLAlchemyError:
        _item_lookup_qty_is_numeric = False
    return _item_lookup_qty_is_numeric


def _coerce_quantity_for_lookup(value):
    raw = str(value or "").strip()
    if not raw:
        return None

    if not _is_item_lookup_quantity_numeric():
        return raw

    # For numeric DB schemas, accept either pure numeric or a leading numeric token (e.g., "10 Pieces").
    try:
        return float(raw)
    except (TypeError, ValueError):
        token = raw.split()[0] if raw.split() else ""
        try:
            return float(token)
        except (TypeError, ValueError):
            return None


def _sync_item_lookup_id_sequence(conn):
    seq_name = conn.execute(
        text("SELECT pg_get_serial_sequence('item_lookup', 'item_lookup_id')")
    ).scalar_one_or_none()
    if not seq_name:
        return
    conn.execute(
        text(
            """
            SELECT setval(
                :seq_name,
                COALESCE((SELECT MAX(item_lookup_id) FROM item_lookup), 1),
                true
            )
            """
        ),
        {"seq_name": seq_name},
    )


# --- Pantry item operations ---

def add_item(barcode):
    """
    Add or increment item by barcode in the item table.
    Returns True on success; False if barcode is unknown.
    """
    _ensure_item_tracking_columns()
    item_lookup = _get_item_lookup_by_barcode(barcode)
    if not item_lookup:
        return False

    item = session.query(Item).where(Item.item_lookup_id == item_lookup.item_lookup_id).first()
    if item:
        item.quantity += 1
        item.last_scanned = datetime.now()
    else:
        session.add(
            Item(
                item_lookup_id=item_lookup.item_lookup_id,
                quantity=1,
                last_scanned=datetime.now(),
            )
        )

    session.commit()
    return True


def remove_item(barcode, quantity=1):
    """
    Decrement quantity or remove row entirely if quantity hits 0.
    Returns True if an item was found and removed/decremented, False otherwise.
    """
    _ensure_item_tracking_columns()
    item_lookup = _get_item_lookup_by_barcode(barcode)
    if not item_lookup:
        return False

    item = session.query(Item).where(Item.item_lookup_id == item_lookup.item_lookup_id).first()
    if not item:
        return False

    if item.quantity > quantity:
        item.quantity -= quantity
        item.last_scanned = datetime.now()
    else:
        session.delete(item)

    session.commit()
    return True


def delete_item(barcode):
    """
    Completely delete this item from pantry regardless of quantity.
    Returns True if deleted, False otherwise.
    """
    item_lookup = _get_item_lookup_by_barcode(barcode)
    if not item_lookup:
        return False

    item = session.query(Item).where(Item.item_lookup_id == item_lookup.item_lookup_id).first()
    if not item:
        return False

    session.delete(item)
    session.commit()
    return True


def get_all_items(category_id=None):
    _ensure_item_tracking_columns()
    q = session.query(Item)
    if category_id is not None:
        q = q.where(Item.storage_categories_id == category_id)
    return q.all()


def get_item_lookup_by_id(item_lookup_id):
    return session.query(ItemLookup).where(ItemLookup.item_lookup_id == item_lookup_id).first()


def get_product_details(barcode):
    """
    Product details for ItemDetailsWindow from PostgreSQL schema provided.
    This schema does not include brand/categories/nutrition columns.
    """
    _ensure_item_lookup_optional_columns()

    item_lookup = _get_item_lookup_by_barcode(barcode)
    if not item_lookup:
        return None

    quantity_name = None
    if item_lookup.quantity_id is not None:
        qty = session.query(Quantity).where(Quantity.quantity_id == item_lookup.quantity_id).first()
        if qty:
            quantity_name = qty.quantity_name

    try:
        with engine.begin() as conn:
            extra = (
                conn.execute(
                    text(
                        """
                        SELECT quantity, brand, categories, energy_kcal_100g, fat_100g,
                               saturated_fat_100g, carbs_100g, sugars_100g, proteins_100g, salt_100g
                        FROM item_lookup
                        WHERE item_lookup_id = :item_lookup_id
                        """
                    ),
                    {"item_lookup_id": item_lookup.item_lookup_id},
                )
                .mappings()
                .first()
            )
        extra = extra or {}
    except SQLAlchemyError:
        extra = {}

    return {
        "name": item_lookup.item_name,
        "description": item_lookup.description,
        "brand": extra.get("brand"),
        "quantity": extra.get("quantity") or quantity_name,
        "categories": extra.get("categories"),
        "energy_kcal_100g": extra.get("energy_kcal_100g"),
        "fat_100g": extra.get("fat_100g"),
        "saturated_fat_100g": extra.get("saturated_fat_100g"),
        "carbs_100g": extra.get("carbs_100g"),
        "sugars_100g": extra.get("sugars_100g"),
        "proteins_100g": extra.get("proteins_100g"),
        "salt_100g": extra.get("salt_100g"),
    }


def add_manual_lookup_and_item(barcode, product_data):
    """
    Create a new item_lookup row for a barcode and add quantity=1 to pantry.
    Optional product metadata values can be null.
    """
    _ensure_item_tracking_columns()
    _ensure_item_lookup_optional_columns()

    barcode_text = str(barcode or "").strip()
    if not barcode_text:
        return False, "Barcode is required."
    if not barcode_text.isdigit():
        return False, "Barcode must contain digits only."

    item_name = str((product_data or {}).get("name") or "").strip()
    if not item_name:
        return False, "Item name is required."

    existing = _get_item_lookup_by_barcode(barcode_text)
    if existing:
        add_item(barcode_text)
        return True, None

    payload = {
        "item_name": item_name,
        "description": str((product_data or {}).get("description") or "").strip() or None,
        "barcode": barcode_text,
        "quantity": _coerce_quantity_for_lookup((product_data or {}).get("quantity")),
        "quantity_id": 1,
        "brand": str((product_data or {}).get("brand") or "").strip() or None,
        "categories": str((product_data or {}).get("categories") or "").strip() or None,
        "energy_kcal_100g": _to_decimal_or_none((product_data or {}).get("energy_kcal_100g")),
        "fat_100g": _to_decimal_or_none((product_data or {}).get("fat_100g")),
        "saturated_fat_100g": _to_decimal_or_none((product_data or {}).get("saturated_fat_100g")),
        "carbs_100g": _to_decimal_or_none((product_data or {}).get("carbs_100g")),
        "sugars_100g": _to_decimal_or_none((product_data or {}).get("sugars_100g")),
        "proteins_100g": _to_decimal_or_none((product_data or {}).get("proteins_100g")),
        "salt_100g": _to_decimal_or_none((product_data or {}).get("salt_100g")),
        "last_scanned": datetime.now(),
    }

    insert_lookup_sql = text(
        """
        INSERT INTO item_lookup (
            item_name, description, barcode, quantity, quantity_id, brand, categories,
            energy_kcal_100g, fat_100g, saturated_fat_100g, carbs_100g,
            sugars_100g, proteins_100g, salt_100g
        )
        VALUES (
            :item_name, :description, :barcode, :quantity, :quantity_id, :brand, :categories,
            :energy_kcal_100g, :fat_100g, :saturated_fat_100g, :carbs_100g,
            :sugars_100g, :proteins_100g, :salt_100g
        )
        RETURNING item_lookup_id
        """
    )
    insert_item_sql = text(
        """
        INSERT INTO item (item_lookup_id, quantity, last_scanned)
        VALUES (:item_lookup_id, :quantity, :last_scanned)
        """
    )

    try:
        with engine.begin() as conn:
            new_lookup_id = conn.execute(insert_lookup_sql, payload).scalar_one()
            conn.execute(
                insert_item_sql,
                {
                    "item_lookup_id": new_lookup_id,
                    "quantity": 1,
                    "last_scanned": payload["last_scanned"],
                },
            )
    except IntegrityError as e:
        # Common legacy DB issue: serial sequence behind max(item_lookup_id).
        msg = str(e).lower()
        if "item_lookup_pkey" in msg:
            try:
                with engine.begin() as conn:
                    _sync_item_lookup_id_sequence(conn)
                    new_lookup_id = conn.execute(insert_lookup_sql, payload).scalar_one()
                    conn.execute(
                        insert_item_sql,
                        {
                            "item_lookup_id": new_lookup_id,
                            "quantity": 1,
                            "last_scanned": payload["last_scanned"],
                        },
                    )
            except Exception as retry_err:
                print(f"Failed to add manual lookup item after sequence sync: {retry_err}")
                return False, "Could not save this item because the database sequence is out of sync."
        else:
            print(f"Failed to add manual lookup item: {e}")
            return False, "Could not save this item. Please verify the form values and try again."
    except Exception as e:
        print(f"Failed to add manual lookup item: {e}")
        return False, "Could not save this item. Please verify the form values and try again."

    session.expire_all()
    return True, None


def get_all_storage_categories():
    cats = session.query(StorageCategory).order_by(StorageCategory.storage_category_name.asc()).all()
    return [(c.storage_categories_id, c.storage_category_name) for c in cats]


def create_storage_category(name):
    name = (name or "").strip()
    if not name:
        return False, None

    existing = session.query(StorageCategory).where(StorageCategory.storage_category_name == name).first()
    if existing:
        return False, existing.storage_categories_id

    new_cat = StorageCategory(storage_category_name=name, quantity_id=1, need_refill=False)
    session.add(new_cat)
    session.commit()
    return True, new_cat.storage_categories_id


def delete_storage_category(category_id):
    cat = session.query(StorageCategory).where(StorageCategory.storage_categories_id == category_id).first()
    if not cat:
        return False
    session.delete(cat)
    session.commit()
    return True


def assign_item_to_category(barcode, category_id):
    _ensure_item_tracking_columns()
    item_lookup = _get_item_lookup_by_barcode(barcode)
    if not item_lookup:
        return False

    items = session.query(Item).where(Item.item_lookup_id == item_lookup.item_lookup_id).all()
    if not items:
        return False

    for item in items:
        item.storage_categories_id = category_id
        item.last_scanned = datetime.now()

    session.commit()
    return True


def get_new_item_lookup_from_api(barcode):
    """
    Fetch item details from UPCItemDB API using the given barcode.
    Creates a new item_lookup record if found, or returns None if not found/error.
    """
    url = "https://api.upcitemdb.com/prod/trial/lookup?" + urlencode({"upc": barcode})
    try:
        with urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
        if data.get("code") == "OK" and data.get("total", 0) > 0:
            item = data["items"][0]
            new_lookup = ItemLookup(
                barcode=int(str(barcode).strip()) if str(barcode).strip().isdigit() else None,
                item_name=item.get("title"),
                description=item.get("description"),
                quantity_id=1,
            )
            session.add(new_lookup)
            session.commit()
            return new_lookup
        return None
    except Exception as e:
        print(f"API error: {e}")
        return None
