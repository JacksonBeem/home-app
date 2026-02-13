# Example: models.py
from sqlalchemy.types import Numeric
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
import database

Base = declarative_base()

class Quantity(Base):
    __tablename__ = 'quantity'
    quantity_id = Column(Integer, primary_key=True)
    quantity_name = Column(String(50))

def create_tables():
    """Create all tables in the database using the engine from database.py."""
    engine = database.engine
    Base.metadata.create_all(engine)