from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

from sqlmodel import Field, Session, SQLModel, create_engine, select


class Track(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    spotify_id: Optional[str] = Field(default=None, index=True)
    title: str
    artist: Optional[str] = None
    album: Optional[str] = None
    # queued | downloading | done | failed | skipped
    status: str = Field(default="queued", index=True)
    file_path: Optional[str] = None
    error_msg: Optional[str] = None
    # playlist | manual
    source: str = Field(default="playlist")
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    downloaded_at: Optional[datetime] = None


class Settings(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    playlist_url: Optional[str] = None
    quality: str = Field(default="320")
    poll_interval_minutes: int = Field(default=60)
    file_template: str = Field(default="{artist} - {title}")
    sleep_between_downloads: int = Field(default=7)
    max_retries: int = Field(default=3)


DB_PATH = os.environ.get("DB_PATH", "/data/db.sqlite")
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


def get_settings(session: Session) -> Settings:
    settings = session.exec(select(Settings)).first()
    if not settings:
        settings = Settings()
        session.add(settings)
        session.commit()
        session.refresh(settings)
    return settings
