from sqlalchemy.orm import sessionmaker
from database import engine
from models.person import Person
from models.chore import Chore
from sqlalchemy import Column, Integer, String, ForeignKey
from models.person import Base
from database import engine

Session = sessionmaker(bind=engine)
session = Session()

class FavoriteFood(Base):
    __tablename__ = "favorite_food"

    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey("person.person_id"))
    food_name = Column(String)

Base.metadata.create_all(engine)

def get_all_members():
    return session.query(Person).order_by(Person.person_id).all()

def add_member(first_name, last_name, gender):
    new_member = Person(
        first_name=first_name,
        last_name=last_name,
        gender=gender
    )

    session.add(new_member)
    session.commit()
    return True

def delete_member(person_id):
    person = session.query(Person).filter(Person.person_id == person_id).first()

    if not person:
        return False
    
    delete_favorites_for_person(person_id)
    session.delete(person)
    session.commit()

    return True

def update_member(person_id, first_name, last_name, gender):

    person = session.query(Person).filter(Person.person_id == person_id).first()

    if person:
        person.first_name = first_name
        person.last_name = last_name
        person.gender = gender

        session.commit()
        return True

    return False

def assign_reminder(person_id, description, frequency):

    # Get next chore_num (simple fix)
    last = session.query(Chore).order_by(Chore.chore_num.desc()).first()
    next_num = 1 if not last else last.chore_num + 1

    new_chore = Chore(
        chore_num=next_num,
        description=description,
        person_id=person_id,
        frequency=frequency,
        priority=1
    )

    session.add(new_chore)
    session.commit()
    return True

def get_reminders_for_person(person_id):
    return session.query(Chore).filter(Chore.person_id == person_id).all()

def delete_reminder_by_id(chore_id):

    reminder = session.query(Chore).filter(Chore.chore_id == chore_id).first()

    if reminder:
        session.delete(reminder)
        session.commit()
        return True

    return False

def assign_favorite_food(person_id, food_name):

    new_food = FavoriteFood(
        person_id=person_id,
        food_name=food_name
    )

    session.add(new_food)
    session.commit()
    return True


def get_favorites_for_person(person_id):
    return session.query(FavoriteFood).filter(FavoriteFood.person_id == person_id).all()

def delete_favorites_for_person(person_id):
    session.query(FavoriteFood).filter(
        FavoriteFood.person_id == person_id
    ).delete()
    session.commit()