from sqlalchemy.orm import sessionmaker
from database import engine
from models.person import Person

Session = sessionmaker(bind=engine)
session = Session()

def get_all_members():
    return session.query(Person).all()

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

    if person:
        session.delete(person)
        session.commit()
        return True

    return False

def update_member(person_id, first_name, last_name, gender):

    person = session.query(Person).filter(Person.person_id == person_id).first()

    if person:
        person.first_name = first_name
        person.last_name = last_name
        person.gender = gender

        session.commit()
        return True

    return False