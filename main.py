from fastapi import FastAPI

from routers.users import router as user_router

app = FastAPI();

@app.get("/")
def root():
    return {"message": "Hej från min första microservice"}

app.include_router(user_router)

