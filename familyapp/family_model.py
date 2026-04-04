# SQLAlchemy setup for database connection and ORM
from sqlalchemy.orm import sessionmaker
from database import engine
# Import models used in this file
from models.person import Person
from models.chore import Chore
# SQL column types and relationships
from sqlalchemy import Column, Integer, String, ForeignKey
# Base class for defining tables
from models.person import Base
from database import engine
from models.person_recipe import PersonRecipe
from models.recipe import Recipe

# Create session to interact with database
Session = sessionmaker(bind=engine)
session = Session()

# Table to store each person's favorite foods
class FavoriteFood(Base):
    __tablename__ = "favorite_food"

    id = Column(Integer, primary_key=True) # Unique ID for each favorite
    person_id = Column(Integer, ForeignKey("person.person_id")) # Link to person
    food_name = Column(String) # Name of favorite food
# Create tables in database if they don't exist
Base.metadata.create_all(engine)

# Retrieve all family members ordered by ID
def get_all_members():
    return session.query(Person).order_by(Person.person_id).all()

# Add a new family member to the database
def add_member(first_name, last_name, gender):
    new_member = Person(
        first_name=first_name,
        last_name=last_name,
        gender=gender
    )

    session.add(new_member)  # Insert into DB
    session.commit() # Save changes
    return True

# Delete a member and their related favorite foods
def delete_member(person_id):
    person = session.query(Person).filter(Person.person_id == person_id).first()

    if not person:
        return False
    
    delete_favorites_for_person(person_id) # Remove related favorites first
    session.delete(person)  # Delete member
    session.commit()

    return True

# Update an existing member's information
def update_member(person_id, first_name, last_name, gender):

    person = session.query(Person).filter(Person.person_id == person_id).first()

    if person:
        person.first_name = first_name
        person.last_name = last_name
        person.gender = gender

        session.commit()
        return True

    return False

# Add a favorite food for a specific member
def assign_favorite_food(person_id, food_name):

    new_food = PersonRecipe(
        person_id=person_id,
        recipe_id=food_name,  # Assuming food_name is actually recipe_id
        is_favorite=True
    )

    session.add(new_food) # Insert into DB
    session.commit()
    return True

# Get all favorite foods for a specific member
def get_favorites_for_person(person_id):
    return session.query(PersonRecipe).where(PersonRecipe.person_id == person_id).where(PersonRecipe.is_favorite).all()

# Delete all favorite foods for a member (used before deleting member)
def delete_favorites_for_person(person_id):
    session.query(PersonRecipe).filter(
        PersonRecipe.person_id == person_id
    ).delete()
    session.commit()

# Delete a single favorite food using its ID
def delete_favorite_by_id(food_id):

    food = session.query(PersonRecipe).filter(PersonRecipe.recipe_id == food_id).first()

    if food:
        session.delete(food) # Remove specific favorite
        session.commit()
        return True
    
    return False

def get_favorite_by_id(food_id):
    return session.query(Recipe).filter(Recipe.recipe_id == food_id).first().recipe_name
    
def writeprofilepicturetodb(person_id, image_data):
    person = session.query(Person).filter(Person.person_id == person_id).first()

    if person:
        person.profile_picture = image_data
        session.commit()
        return True
    
    return False

def getallrecipes():
    return session.query(Recipe).all()