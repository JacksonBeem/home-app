from sqlalchemy.orm import sessionmaker
from database import engine
from models.chore import Chore

Session = sessionmaker(bind=engine)
session = Session()

def get_all_chores():
    chores = session.query(Chore).order_by(Chore.chore_num).all()
    return chores

def add_chore(description, person_id, frequency):
    # Calculate the next number (Total chores + 1)
    current_count = session.query(Chore).count()
    new_num = current_count + 1

    new_chore = Chore(
        chore_num=new_num,
        description=description,
        person_id=person_id,
        frequency=frequency
    )
    session.add(new_chore)
    session.commit()
    return True

def delete_chore(target_num: int):
    # 1. Find the chore using the chore_num (the number the user sees)
    chore_to_delete = session.query(Chore).filter(Chore.chore_num == target_num).first()
    
    if chore_to_delete:
        # 2. Delete the record
        session.delete(chore_to_delete)
        session.commit()
        
        # 3. RE-SEQUENCE: Fetch all remaining chores ordered by their current number
        remaining_chores = session.query(Chore).order_by(Chore.chore_num).all()
        
        # 4. Loop through and assign new sequential numbers (1, 2, 3...)
        for index, chore in enumerate(remaining_chores, start=1):
            chore.chore_num = index
            
        # 5. Save the new sequence to the database
        session.commit()
        return True
        
    return False

def set_chore_priority(target_num: int, new_priority: int):
    """Updates the priority of a specific chore."""
    chore = session.query(Chore).filter(Chore.chore_num == target_num).first()
    
    if chore:
        chore.priority = new_priority
        session.commit()
        return True
    return False