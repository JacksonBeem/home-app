# Example: models.py
from sqlalchemy.types import Numeric
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
import database

Base = declarative_base()

class PersonRecipe(Base):
    __tablename__ = 'person_recipe'
    person_recipe_id = Column(Integer, primary_key=True)
    person_id = Column(Integer)
    recipe_id = Column(Integer)
    is_favorite = Column(Boolean, default=False)

def create_tables():
    """Create all tables in the database using the engine from database.py."""
    engine = database.engine
    Base.metadata.create_all(engine)