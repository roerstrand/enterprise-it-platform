from sqlalchemy import select
from sqlalchemy.orm import Session

from data.models.user_model import UserModel

def get_all_users_from_db(db: Session):
    return db.execute(select(UserModel)).scalars().all()

       


def get_user_by_id_from_db(db: Session, user_id):
    return db.execute(
        select(UserModel).where(UserModel.id == user_id)
    ).scalars().first()
    
    

    
def create_user_in_db(db: Session, name, email):
    user = UserModel(name=name, email=email)
    db.add(user)
    db.commit()
    return user
    

def delete_user_from_db(db: Session, user_id):
    user = db.execute(
        select(UserModel).where(UserModel.id == user_id)
    ).scalars().first()
    db.delete(user)
    db.commit()
  

def update_user_in_db(db: Session, user_id: int, name: str, email: str):
    user = db.execute(
        select(UserModel).where(UserModel.id == user_id)
    ).scalars().first()
    user.name = name
    user.email = email
    db.commit()
    return user

