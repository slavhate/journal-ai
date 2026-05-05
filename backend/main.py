import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.config import FRONTEND_DIR
from backend.database import init_db
from backend.routers.entries import router as entries_router
from backend.routers.days import router as days_router
from backend.routers.today import router as today_router
from backend.routers.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Journal AI", lifespan=lifespan)

_allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:8550").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type"],
)

app.include_router(entries_router)
app.include_router(days_router)
app.include_router(today_router)
app.include_router(health_router)

app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
