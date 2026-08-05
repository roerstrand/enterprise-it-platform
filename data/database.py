from dotenv import load_dotenv
load_dotenv()

import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator

from contextlib import asynccontextmanager

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/users.db")

engine = create_async_engine(DATABASE_URL)

SessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()

get_db_context = asynccontextmanager(get_db)
