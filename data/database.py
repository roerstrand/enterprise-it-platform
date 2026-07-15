from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

engine = create_engine(
    "sqlite:///./data/users.db"
)

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

        