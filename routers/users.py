from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from data.database import get_db

from schemas.user_create import UserCreateSchema
from schemas.user_response import UserResponseSchema
from schemas.user_update import UserUpdateSchema

from services.user_service import (
    get_all_users,
    get_user_by_id,
    create_user,
    delete_user_by_id,
    update_user
)

router = APIRouter();

@router.get("/users", response_model=list[UserResponseSchema])
def get_users(db: Session = Depends(get_db)):
    return get_all_users(db)

@router.get("/users/{user_id}", response_model=UserResponseSchema)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="Användaren hittades inte")
    
    return user

@router.post("/users", response_model=UserResponseSchema)
def add_user(user: UserCreateSchema, db: Session = Depends(get_db)):
    return create_user(db, user.name, user.email)

@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="Användaren hittades inte")
    delete_user_by_id(db, user_id)

@router.put("/users/{user_id}", response_model=UserResponseSchema)
def update_user_endpoint(user_id: int, user: UserUpdateSchema, db: Session = Depends(get_db)):
    existing = get_user_by_id(db, user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Användaren hittades inte")
    return update_user(db, user_id, user.name, user.email)

