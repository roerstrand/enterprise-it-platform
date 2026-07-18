from fastapi import FastAPI

app = FastAPI();

@app.get("/")
def root():
    return {"message": "Hej från min första microservice"}
