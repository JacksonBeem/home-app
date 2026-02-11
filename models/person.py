# Example: models.py
from sqlalchemy.types import Numeric
from sqlalchemy import Boolean, Column, Date, Integer, String
from sqlalchemy.ext.declarative import declarative_base
import database

Base = declarative_base()

class Person(Base):
    __tablename__ = 'person'
    person_id = Column(Integer, primary_key=True)
    is_parent = Column(Boolean, default=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    date_of_birth = Column(Date)
    gender = Column(String(50))

def create_tables():
    """Create all tables in the database using the engine from database.py."""
    engine = database.engine
    Base.metadata.create_all(engine)