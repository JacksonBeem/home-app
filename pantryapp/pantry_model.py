import sqlite3
from datetime import datetime
from database import get_connection, _lookup_display_name

# --- Pantry item operations ---

def add_item(barcode):
    """
    Add or increment item by barcode in the items table.
    Returns True on success, False if the product barcode is unknown.
    """
    now = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        display_name = _lookup_display_name(conn, barcode)
        if display_name is None:
            return False

        c = conn.cursor()
        c.execute("SELECT quantity FROM items WHERE barcode = ?", (barcode,))
        row = c.fetchone()

        if row:
            # Item exists, increment quantity
            new_qty = row[0] + 1
            c.execute("""
                UPDATE items
                SET quantity = ?, last_scanned = ?
                WHERE barcode = ?
            """, (new_qty, now, barcode))
        else:
            # New item, insert with quantity 1
            c.execute("""
                INSERT INTO items (barcode, name, quantity, last_scanned, category_id)
                VALUES (?, ?, ?, ?, NULL)
            """, (barcode, display_name, 1, now))

        conn.commit()
        return True


def remove_item(barcode):
    """
    Decrement quantity or remove row entirely if quantity hits 0.
    Returns True if an item was found and removed/decremented, False otherwise.
    """
    now = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT quantity FROM items WHERE barcode = ?", (barcode,))
        row = c.fetchone()
        if not row:
            return False

        qty = row[0]
        if qty > 1:
            new_qty = qty - 1
            c.execute("""
                UPDATE items
                SET quantity = ?, last_scanned = ?
                WHERE barcode = ?
            """, (new_qty, now, barcode))
        else:
            # Quantity is 1, delete the item
            c.execute("DELETE FROM items WHERE barcode = ?", (barcode,))

        conn.commit()
        return True


def delete_item(barcode):
    """
    Completely delete this item from the pantry (items table), regardless of its quantity.
    Returns True if an item was deleted, False otherwise.
    """
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM items WHERE barcode = ?", (barcode,))
        conn.commit()
        return c.rowcount > 0


def get_all_items(category_id=None):
    """
    Return all pantry items as a list of:
      (barcode, name, location_name, last_scanned, quantity)
    If category_id is provided, filters by that storage category.
    """
    with get_connection() as conn:
        c = conn.cursor()

        base_sql = """
            SELECT
                i.barcode,
                i.name,
                COALESCE(sc.name, '') AS display_location,
                i.last_scanned,
                i.quantity
            FROM items i
            LEFT JOIN storage_categories sc
              ON i.category_id = sc.id
        """

        params = ()
        if category_id is not None:
            base_sql += " WHERE i.category_id = ?"
            params = (category_id,)

        base_sql += " ORDER BY i.name COLLATE NOCASE"

        c.execute(base_sql, params)
        return c.fetchall()


# --- Storage category operations ---

def get_all_storage_categories():
    """Return list of (id, name) for all storage categories."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT id, name
            FROM storage_categories
            ORDER BY name COLLATE NOCASE
        """)
        return c.fetchall()


def create_storage_category(name):
    """
    Create a new storage category.
    Returns (True, id) on success, (False, id) on failure (e.g., already exists).
    """
    name = (name or "").strip()
    if not name:
        return False, None

    with get_connection() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT OR IGNORE INTO storage_categories (name)
            VALUES (?)
        """, (name,))
        conn.commit()

        if c.rowcount > 0:
            return True, c.lastrowid
        else:
            # Must have been a conflict, fetch existing ID
            c.execute("SELECT id FROM storage_categories WHERE name = ?", (name,))
            row = c.fetchone()
            return False, row[0] if row else None


def delete_storage_category(category_id):
    """
    Delete a storage category and clear it from any items that used it.
    Returns True on success.
    """
    with get_connection() as conn:
        c = conn.cursor()
        # Clear category on items first
        c.execute("UPDATE items SET category_id = NULL WHERE category_id = ?", (category_id,))
        # Then delete category
        c.execute("DELETE FROM storage_categories WHERE id = ?", (category_id,))
        conn.commit()
        return True


def assign_item_to_category(barcode, category_id):
    """
    Assign the given pantry item (by barcode) to a storage category.
    category_id may be None to clear the category.
    Returns True if an item was updated, False otherwise.
    """
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("""
            UPDATE items
            SET category_id = ?
            WHERE barcode = ?
        """, (category_id, barcode))
        conn.commit()
        return c.rowcount > 0


# --- Product nutrition details ---

def get_product_details(barcode):
    """
    Fetch detailed nutrition information from the 'products' table.
    Returns a dictionary of product details or None if the barcode is not found.
    """
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("""
            SELECT
                code, name, brand, quantity, categories,
                energy_kcal_100g, fat_100g, saturated_fat_100g,
                carbs_100g, sugars_100g, proteins_100g, salt_100g,
                last_modified_t
            FROM products
            WHERE code = ?
        """, (barcode,))

        row = c.fetchone()
        if not row:
            return None

        return dict(row)
