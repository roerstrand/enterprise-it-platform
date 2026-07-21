from dotenv import load_dotenv
load_dotenv()

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from contextlib import contextmanager

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/users.db")

engine = create_engine(
DATABASE_URL)

SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False
)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

get_db_context = contextmanager(get_db)