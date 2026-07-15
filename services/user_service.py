from sqlalchemy.orm import Session

from repositories.user_repository import (
    get_all_users_from_db,
    get_user_by_id_from_db,
    create_user_in_db,
    delete_user_from_db,
    update_user_in_db
)


def get_all_users(db: Session):
    return get_all_users_from_db(db)


def get_user_by_id(db: Session, user_id):
    return get_user_by_id_from_db(db, user_id)


def create_user(db: Session, name, email):
    return create_user_in_db(db, name, email)

def delete_user_by_id(db: Session, user_id):
    return delete_user_from_db(db, user_id)

def update_user(db: Session, user_id: int, name: str, email: str):
    return update_user_in_db(db, user_id, name, email)