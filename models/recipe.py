# Example: models.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
import database

Base = declarative_base()

class Recipe(Base):
    __tablename__ = 'recipe'
    recipe_id = Column(Integer, primary_key=True)
    recipe_name = Column(String)
    is_favorite = Column(bool, nullable=False)

def create_tables():
    """Create all tables in the database using the engine from database.py."""
    engine = database.engine
    Base.metadata.create_all(engine)