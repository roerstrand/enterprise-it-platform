from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from routers import demo
from middleware.security_headers import SecurityHeadersMiddleware

from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI();

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://localhost.4200"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(demo.router)

Instrumentator().instrument(app).expose(app)

@app.get("/")
def root():
    return {"message": "Hello from my first microservice"}
