import sqlite3
from datetime import datetime
from models.item import Item
from models.item_lookup import ItemLookup
from sqlalchemy.orm import sessionmaker
from database import get_connection, engine
import json
from urllib.request import urlopen
from urllib.parse import urlencode

Session = sessionmaker(bind=engine)
session = Session()

# --- Pantry item operations ---

def add_item(barcode):
    """
    Add or increment item by barcode in the items table.
    Returns True on success, if the product barcode is unknown, 
    another function will need to be used to add it through an api call.
    """
    item_lookup = session.query(ItemLookup).where(ItemLookup.barcode == barcode).first()
    if not item_lookup:
        return False  # Unknown barcode this needs to be update to make api call to add new item_lookup
    item = session.query(Item).where(Item.item_lookup_id == item_lookup.item_lookup_id).first()
    if item: # if the item already exists, increment quantity
        item.quantity += 1
    else: # else create a new item entry
        new_item = Item(
            item_lookup_id=item_lookup.item_lookup_id,
            quantity=1
        )
        session.add(new_item)
    session.commit()
    return True


def remove_item(barcode, quantity=1):
    """
    Decrement quantity or remove row entirely if quantity hits 0.
    Returns True if an item was found and removed/decremented, False otherwise.
    """
    item_lookup = session.query(ItemLookup).where(ItemLookup.barcode == barcode).first()
    if not item_lookup:
        return False  # Unknown barcode. What should we do here?
    else:
        item = session.query(Item).where(Item.item_lookup_id == item_lookup.item_lookup_id).first()
        if item:
            if item.quantity > quantity:
                item.quantity -= quantity
            else:
                session.delete(item)
            session.commit()
            return True
    return False

def delete_item(barcode):
    """
    Completely delete all of this item from the pantry (item table), regardless of its quantity.
    Returns True if an item was deleted, False otherwise.
    """
    item_lookup = session.query(ItemLookup).where(ItemLookup.barcode == barcode).first()
    if not item_lookup:
        return False  # Unknown barcode. What should we do here?
    else:
        item = session.query(Item).where(Item.item_lookup_id == item_lookup.item_lookup_id).first()
        if item:
            session.delete(item)
            session.commit()
            return True
    return False


def get_all_items(category_id=None):
    items = session.query(Item).all()
    return items

def get_item_lookup_by_id(item_lookup_id):
    item_lookups = session.query(ItemLookup).where(ItemLookup.item_lookup_id == item_lookup_id).first()
    return item_lookups

def get_new_item_lookup_from_api(barcode):
    """
    Fetch item details from UPCItemDB API using the given barcode.
    Creates a new item_lookup record if found, or returns None if not found or error.
    """
    url = "https://api.upcitemdb.com/prod/trial/lookup?" + urlencode({"upc": barcode})
    try:
        with urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
        if data.get("code") == "OK" and data.get("total", 0) > 0:
            item = data["items"][0]
            # Create new ItemLookup record
            new_lookup = ItemLookup(
                barcode=barcode,
                item_name=item.get("title"),
                description=item.get("description"),
            )
            session.add(new_lookup)
            session.commit()
            return new_lookup
        else:
            return None
    except Exception as e:
        print(f"API error: {e}")
        return None
