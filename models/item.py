# Example: models.py
from sqlalchemy.types import Numeric
from sqlalchemy import Column, Integer
from sqlalchemy.ext.declarative import declarative_base
import database

Base = declarative_base()

class Item(Base):
    __tablename__ = 'item'
    item_id = Column(Integer, primary_key=True)
    item_lookup_id = Column(Integer)
    quantity = Column(Numeric(10, 2), nullable=False)

def create_tables():
    """Create all tables in the database using the engine from database.py."""
    engine = database.engine
    Base.metadata.create_all(engine)