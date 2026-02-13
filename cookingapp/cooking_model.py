# cooking_model.py
# Data/model logic for CookingApp
import sqlite3
from datetime import datetime
from models.item import Item
from models.item_lookup import ItemLookup
from models.person import Person
from models.recipe import Recipe
from models.person_recipe import PersonRecipe
from sqlalchemy.orm import sessionmaker
from database import get_connection, engine
import json
from urllib.request import urlopen
from urllib.parse import urlencode

Session = sessionmaker(bind=engine)
session = Session()

class RecipeManager:
    def __init__(self):
        self._recipes = []
        self._next_id = 1

    def add_recipe(self, recipe):
        recipe = dict(recipe)
        recipe['id'] = self._next_id
        self._next_id += 1
        self._recipes.append(recipe)

    def remove_recipe(self, recipe_id):
        self._recipes = [r for r in self._recipes if r.get('id') != recipe_id]

    def get_all_recipes(self):
        return session.query(Recipe).all()
        #return list(self._recipes)

    def get_favorite_recipes(self, person_id):
        person = session.query(Person).where(Person.person_id == person_id).first()
        if not person:
            return []
        person_recipes = session.query(PersonRecipe).where(PersonRecipe.person_id == person_id and PersonRecipe.is_favorite == True).all()
        fav_recipe_ids = {pr.recipe_id for pr in person_recipes if pr.is_favorite}
        return session.query(Recipe).where(Recipe.recipe_id.in_(fav_recipe_ids)).all()
    
    def get_all_people(self):
        return session.query(Person).all()

# Add more model classes as needed
