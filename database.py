# database.py
import sqlite3
from datetime import datetime

# --- Configuration ---
DB_NAME = "openfoodfacts_slim.db"

# --- Connection Management ---
def get_connection():
    """Returns a new SQLite connection object."""
    return sqlite3.connect(DB_NAME)

def init_db_schema():
    """Initializes the database schema for the pantry items and storage categories."""
    with get_connection() as conn:
        c = conn.cursor()

        # items table
        c.execute("""
            CREATE TABLE IF NOT EXISTS items (
                barcode TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                last_scanned TEXT
            )
        """)

        # storage_categories table for dynamic locations
        c.execute("""
            CREATE TABLE IF NOT EXISTS storage_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)

        # Check and add category_id column if it doesn't exist (Migration logic)
        c.execute("PRAGMA table_info(items)")
        cols = [row[1] for row in c.fetchall()]
        if "category_id" not in cols:
            # Added FOREIGN KEY for better schema
            c.execute("ALTER TABLE items ADD COLUMN category_id INTEGER REFERENCES storage_categories(id)") 
        
        conn.commit()


def _lookup_display_name(conn, barcode):
    """
    Builds a human-readable display name from the OpenFoodFacts 'products' table.
    Retries with a leading zero if the barcode is not found.
    """
    c = conn.cursor()
    
    # --- Attempt 1: Standard barcode ---
    c.execute("""
        SELECT name, brand, quantity
        FROM products
        WHERE code = ?
    """, (barcode,))
    row = c.fetchone()

    # --- Attempt 2: Fallback to leading zero ---
    if not row:
        c.execute("""
            SELECT name, brand, quantity
            FROM products
            WHERE code = ?
        """, ("0" + barcode,))
        row = c.fetchone()

    if not row:
        return None

    name, brand, pack_qty = row
    
    parts = [str(p) for p in (brand, name) if p]
    if pack_qty:
        parts.append(f"({pack_qty})")

    display_name = " ".join(parts) if parts else f"Unknown product {barcode}"
    return display_name