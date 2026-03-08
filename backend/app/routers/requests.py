from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from ..database import Track, get_session

router = APIRouter()


class RequestBody(BaseModel):
    query: str


@router.post("/requests", status_code=201)
def create_request(body: RequestBody, session: Session = Depends(get_session)):
    q = body.query.strip()
    if not q:
        raise HTTPException(status_code=400, detail="query must not be empty")

    # Attempt to split "Artist - Title" format
    if " - " in q:
        parts = q.split(" - ", 1)
        artist, title = parts[0].strip(), parts[1].strip()
    else:
        artist, title = None, q

    track = Track(
        title=title,
        artist=artist,
        status="queued",
        source="manual",
    )
    session.add(track)
    session.commit()
    session.refresh(track)
    return track
