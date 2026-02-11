# Example: models.py
from sqlalchemy.types import Numeric
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
import database

Base = declarative_base()

class Family(Base):
    __tablename__ = 'family'
    family_id = Column(Integer, primary_key=True)
    family_name = Column(String(255))

def create_tables():
    """Create all tables in the database using the engine from database.py."""
    engine = database.engine
    Base.metadata.create_all(engine)