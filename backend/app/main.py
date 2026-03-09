from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import create_db_and_tables
from .routers import auth, downloads, playlists, requests, settings, status, upload
from .routers import import_csv as import_csv_router
from .scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="Spotify Downloader", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(downloads.router, prefix="/api")
app.include_router(playlists.router, prefix="/api")
app.include_router(requests.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(status.router, prefix="/api")
app.include_router(import_csv_router.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
