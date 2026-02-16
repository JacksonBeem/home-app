from sqlalchemy.orm import sessionmaker
from database import engine
from models.chore import Chore

Session = sessionmaker(bind=engine)
session = Session()

def get_all_chores():
    chores = session.query(Chore).all()
    return chores

def add_chore(description, person_id, frequency):
    new_chore = Chore(
        description=description,
        person_id=person_id,
        frequency=frequency
    )
    session.add(new_chore)
    session.commit()
    return True

def delete_chore(target_id: int):
    chore = session.query(Chore).filter(Chore.chore_id == target_id).first()
    
    if chore:
        session.delete(chore)
        session.commit()
        return True
    return False