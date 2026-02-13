# Example: models.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
import database

Base = declarative_base()

class ItemLookup(Base):
    __tablename__ = 'item_lookup'
    item_lookup_id = Column(Integer, primary_key=True)
    item_name = Column(String(255), nullable=False)
    description = Column(String(500))
    barcode = Column(String(12), unique=True, nullable=False)

def create_tables():
    """Create all tables in the database using the engine from database.py."""
    engine = database.engine
    Base.metadata.create_all(engine)