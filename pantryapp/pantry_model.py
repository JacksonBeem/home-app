import sqlite3
from datetime import datetime
from database import get_connection

# --- Pantry item operations ---

def add_item(barcode):
    """
    Add or increment item by barcode in the items table.
    Returns True on success, False if the product barcode is unknown.
    """
    with get_connection() as conn:
        c = conn.cursor()
        # Find item_lookup_id for this barcode
        c.execute("SELECT item_lookup_id FROM item_lookup WHERE barcode = %s", (barcode,))
        row = c.fetchone()
        if not row:
            return False
        item_lookup_id = row[0]

        # Check if item already exists
        c.execute("SELECT item_id, quantity FROM item WHERE item_lookup_id = %s", (item_lookup_id,))
        item_row = c.fetchone()
        if item_row:
            # Increment quantity
            new_qty = float(item_row[1]) + 1
            c.execute("UPDATE item SET quantity = %s WHERE item_id = %s", (new_qty, item_row[0]))
        else:
            # Insert new item with quantity 1
            c.execute("INSERT INTO item (item_lookup_id, quantity) VALUES (%s, %s)", (item_lookup_id, 1))
        conn.commit()
        return True


def remove_item(barcode):
    """
    Decrement quantity or remove row entirely if quantity hits 0.
    Returns True if an item was found and removed/decremented, False otherwise.
    """
    with get_connection() as conn:
        c = conn.cursor()
        # Find item_lookup_id for this barcode
        c.execute("SELECT item_lookup_id FROM item_lookup WHERE barcode = %s", (barcode,))
        row = c.fetchone()
        if not row:
            return False
        item_lookup_id = row[0]

        # Find item
        c.execute("SELECT item_id, quantity FROM item WHERE item_lookup_id = %s", (item_lookup_id,))
        item_row = c.fetchone()
        if not item_row:
            return False
        qty = float(item_row[1])
        if qty > 1:
            new_qty = qty - 1
            c.execute("UPDATE item SET quantity = %s WHERE item_id = %s", (new_qty, item_row[0]))
        else:
            c.execute("DELETE FROM item WHERE item_id = %s", (item_row[0],))
        conn.commit()
        return True


def delete_item(barcode):
    """
    Completely delete this item from the pantry (item table), regardless of its quantity.
    Returns True if an item was deleted, False otherwise.
    """
    with get_connection() as conn:
        c = conn.cursor()
        # Find item_lookup_id for this barcode
        c.execute("SELECT item_lookup_id FROM item_lookup WHERE barcode = %s", (barcode,))
        row = c.fetchone()
        if not row:
            return False
        item_lookup_id = row[0]
        # Delete from item table
        c.execute("DELETE FROM item WHERE item_lookup_id = %s", (item_lookup_id,))
        conn.commit()
        return c.rowcount > 0


def get_all_items(category_id=None):
    """
    Return all pantry items as a list of:
      (item_id, item_name, description, barcode, quantity)
    """
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT
                i.item_id,
                il.item_name,
                il.description,
                il.barcode,
                i.quantity
            FROM item i
            JOIN item_lookup il ON i.item_lookup_id = il.item_lookup_id
            ORDER BY il.item_name
            """
        )
        return c.fetchall()


