from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, func, select

from ..database import Track, get_session

router = APIRouter()


@router.get("/downloads")
def list_downloads(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    source: Optional[str] = None,
    session: Session = Depends(get_session),
):
    query = select(Track)
    if status:
        query = query.where(Track.status == status)
    if source:
        query = query.where(Track.source == source)

    total = session.exec(select(func.count()).select_from(query.subquery())).one()
    items = session.exec(
        query.order_by(Track.requested_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()

    return {"items": items, "total": total, "page": page, "limit": limit}
