from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data.models.user_model import UserModel

async def get_all_users_from_db(db: AsyncSession):
    result = await db.execute(select(UserModel))
    return result.scalars().all()

async def get_user_by_id_from_db(db: AsyncSession, user_id):
    result = await db.execute(
        select(UserModel).where(UserModel.id == user_id)
    )
    return result.scalars().first()

async def get_user_by_email_from_db(db: AsyncSession, email: str):
    result = await db.execute(
        select(UserModel).where(UserModel.email == email)
    )
    return result.scalars().first()

async def create_user_in_db(db: AsyncSession, name, email, hashed_password):
    user = UserModel(name=name, email=email, hashed_password=hashed_password)
    db.add(user)
    await db.commit()
    return user

async def delete_user_from_db(db: AsyncSession, user_id):
    result = await db.execute(
        select(UserModel).where(UserModel.id == user_id)
    )
    user = result.scalars().first()
    await db.delete(user)
    await db.commit()

async def update_user_in_db(db: AsyncSession, user_id: int, name: str, email: str):
    result = await db.execute(
        select(UserModel).where(UserModel.id == user_id)
    )
    user = result.scalars().first()
    user.name = name
    user.email = email
    await db.commit()
    return user
