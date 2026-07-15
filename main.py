from fastapi import FastAPI

from routers.users import router as user_router
from data.database import engine
from data.models.user_model import Base

Base.metadata.create_all(bind=engine)

app = FastAPI();

@app.get("/")
def root():
    return {"message": "Hej från min första microservice"}

app.include_router(user_router)

