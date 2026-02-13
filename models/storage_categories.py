# Example: models.py
from sqlalchemy.types import Numeric
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
import database

Base = declarative_base()

class StorageCategory(Base):
    __tablename__ = 'storage_categories'
    storage_categories_id = Column(Integer, primary_key=True)
    storage_categories_name = Column(String(100))
    quantity_id = Column(Integer)
    need_refill = Column(Boolean, default=False)

def create_tables():
    """Create all tables in the database using the engine from database.py."""
    engine = database.engine
    Base.metadata.create_all(engine)