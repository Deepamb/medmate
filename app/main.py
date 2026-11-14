import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from . import models  # noqa: F401
from .database import Base, engine
from .routers import auth_routes, doses, medicines
from .scheduler import scheduler

STATIC = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    run_scheduler = not os.getenv("DISABLE_SCHEDULER")  # tests turn it off
    if run_scheduler:
        scheduler.start()
    yield
    if run_scheduler:
        scheduler.shutdown(wait=False)


app = FastAPI(title="MedMate", description="Medicine reminder and expiry tracker", lifespan=lifespan)
app.include_router(auth_routes.router)
app.include_router(medicines.router)
app.include_router(doses.router)


@app.get("/health")
def health():
    return {"status": "MedMate is running"}


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(STATIC / "index.html")