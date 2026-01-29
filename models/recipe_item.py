# Example: models.py
from sqlalchemy.types import Numeric
from sqlalchemy import Column, Integer
from sqlalchemy.ext.declarative import declarative_base
import database

Base = declarative_base()

class RecipeItem(Base):
    __tablename__ = 'recipe_item'
    recipe_item_id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer)
    item_id = Column(Integer)
    item_quantity = Column(Numeric(10, 2), nullable=False)

def create_tables():
    """Create all tables in the database using the engine from database.py."""
    engine = database.engine
    Base.metadata.create_all(engine)