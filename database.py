# database.py
#import sqlite3
import psycopg2
from sqlalchemy import create_engine
from datetime import datetime


# --- Configuration ---
DB_NAME = "openfoodfacts_slim.db"
SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://postgres:password@localhost:5432/homeappdb"

# SQLAlchemy engine for ORM usage
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# --- Connection Management ---
def get_connection():
    # Setup a connection to the PostgreSQL database
    try:
        connection = psycopg2.connect(
            host="localhost",
            database="homeappdb",
            user="postgres",
            password="password",
            port="5432" # Default PostgreSQL port
        )
        return connection
    except psycopg2.Error as e:
        print(f"An error occurred: {e}")
        return None

def _lookup_display_name(conn, barcode): # not accessed right now
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