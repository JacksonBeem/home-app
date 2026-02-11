# Example: models.py
from sqlalchemy.types import Numeric
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
import database

Base = declarative_base()

class PersonFamily(Base):
    __tablename__ = 'person_family'
    family_id = Column(Integer)
    person_id = Column(Integer)

def create_tables():
    """Create all tables in the database using the engine from database.py."""
    engine = database.engine
    Base.metadata.create_all(engine)