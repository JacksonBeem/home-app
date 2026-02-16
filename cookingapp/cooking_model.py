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
import requests
import psycopg2
from psycopg2 import sql
import io

Session = sessionmaker(bind=engine)
session = Session()

class RecipeManager:
    def __init__(self):
        self._recipes = []
        self._next_id = 1

    # Not currently used, but could be helpful for future features like recipe deletion.
    def remove_recipe(self, recipe_id):
        self._recipes = [r for r in self._recipes if r.get('id') != recipe_id]

    def get_all_recipes(self):
        # equivalent query:
        # Select *
        # From recipe
        return session.query(Recipe).all()
        #return list(self._recipes)

    def get_favorite_recipes(self, person_id):
        # equivalent query:
        # Select * 
        # From person p 
        # Where p.person_id = {input_person_id}
        person = session.query(Person).where(Person.person_id == person_id).first()
        if not person:
            return []
        # equivalent query:
        # Select * 
        # From person_recipe pr 
        # Where pr.person_id = {input_person_id} 
        #     AND pr.is_favorite
        person_recipes = session.query(PersonRecipe).where(PersonRecipe.person_id == person_id and PersonRecipe.is_favorite == True).all()
        fav_recipe_ids = {pr.recipe_id for pr in person_recipes if pr.is_favorite}
        # equivalent query:
        # Select * 
        # From recipe r 
        # Where r.recipe_id IN {input_fav_recipe_ids}
        return session.query(Recipe).where(Recipe.recipe_id.in_(fav_recipe_ids)).all()
    
    def get_all_people(self):
        # equivalent query:
        # Select * 
        # From person 
        return session.query(Person).all()
    
    def fetch_recipe(self, item_name):
        url = f'https://www.themealdb.com/api/json/v1/1/search.php?s={item_name}'
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if not data['meals']:
            raise ValueError(f"No recipe found for {item_name}")
        self.transform_recipe(data['meals'][0])

    # --- TRANSFORM ---
    def transform_recipe(self, meal):
        import random
        recipe = {
            'recipe_name': meal.get('strMeal'),
            'prep_time': round(random.uniform(10, 30), 2),
            'cook_time': round(random.uniform(10, 30), 2),
            'instructions': meal.get('strInstructions'),
            'video_url': meal.get('strYoutube'),
            'image_url': meal.get('strMealThumb')
        }
        self.fetch_image_as_jpeg(recipe, recipe['image_url'])

    def fetch_image_as_jpeg(self, meal, url):
        if not url:
            return None
        response = requests.get(url)
        response.raise_for_status()
        self.load_recipe_to_db(meal, response.content)

    # --- LOAD ---
    def load_recipe_to_db(self, recipe, image_bytes):
        # equivalent query:
        # Insert into recipe (recipe_name, prep_time, cook_time, instructions, video_url, image)
        # Values ({input_recipe_name}, {input_prep_time}, {input_cook_time}, {input_instructions}, {input_video_url}, {input_image_bytes})
        newRecipe = Recipe(
            recipe_name=recipe['recipe_name'],
            prep_time=recipe['prep_time'],
            cook_time=recipe['cook_time'],
            instructions=recipe['instructions'],
            video_url=recipe['video_url'],
            image=image_bytes if image_bytes else None
        )
        session.add(newRecipe)
        session.commit()