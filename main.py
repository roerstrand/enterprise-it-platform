from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from routers import demo
from middleware.security_headers import SecurityHeadersMiddleware

app = FastAPI();

app.add_middleware(SecurityHeadersMiddleware)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(demo.router)

@app.get("/")
def root():
    return {"message": "Hello from my first microservice"}
