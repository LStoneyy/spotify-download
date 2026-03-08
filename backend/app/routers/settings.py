from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session
from typing import Optional

from ..database import Settings, get_session, get_settings

router = APIRouter()


class SettingsUpdate(BaseModel):
    quality: Optional[str] = None
    file_template: Optional[str] = None
    sleep_between_downloads: Optional[int] = None
    max_retries: Optional[int] = None


@router.get("/settings")
def read_settings(session: Session = Depends(get_session)):
    return get_settings(session)


@router.put("/settings")
def update_settings(body: SettingsUpdate, session: Session = Depends(get_session)):
    settings = get_settings(session)

    if body.quality is not None:
        settings.quality = body.quality
    if body.file_template is not None:
        settings.file_template = body.file_template
    if body.sleep_between_downloads is not None:
        settings.sleep_between_downloads = body.sleep_between_downloads
    if body.max_retries is not None:
        settings.max_retries = body.max_retries

    session.add(settings)
    session.commit()
    session.refresh(settings)
    return settings
