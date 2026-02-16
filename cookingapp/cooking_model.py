# cooking_model.py
# Data/model logic for CookingApp
from random import random
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
        self.load_recipe_to_db(meal, response.content)  # Already JPEG

    # --- LOAD ---
    def load_recipe_to_db(self, recipe, image_bytes):
        # conn = psycopg2.connect(**DB_CONFIG)
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

    def fetch_random_by_category(self, category, parent=None):
        url = f'https://www.themealdb.com/api/json/v1/1/filter.php?c={category}'
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if not data['meals']:
            raise ValueError(f"No recipes found for category {category}")
        import random
        meals = random.sample(data['meals'], min(10, len(data['meals'])))
        # Show in CategoryWindow for selection
        from tkinter import messagebox
        from cookingapp.gui_windows import CategoryWindow
        def on_meal_select(meal_name):
            try:
                self.fetch_recipe(meal_name)
                messagebox.showinfo("Recipe Fetched", f"Fetched recipe for {meal_name}")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        win_parent = parent if parent is not None else None
        CategoryWindow(win_parent, meals, on_meal_select, category_name=category)