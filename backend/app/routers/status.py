from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session, func, select

from ..database import Track, get_session
from ..scheduler import get_current_state, poll_playlist

router = APIRouter()


@router.get("/status")
def get_status(session: Session = Depends(get_session)):
    state = get_current_state()

    total_done = session.exec(
        select(func.count()).where(Track.status == "done")
    ).one()
    total_failed = session.exec(
        select(func.count()).where(Track.status == "failed")
    ).one()
    queue_length = session.exec(
        select(func.count()).where(Track.status == "queued")
    ).one()
    total_skipped = session.exec(
        select(func.count()).where(Track.status == "skipped")
    ).one()

    return {
        **state,
        "total_done": total_done,
        "total_failed": total_failed,
        "total_skipped": total_skipped,
        "queue_length": queue_length,
    }


@router.post("/sync")
def trigger_sync():
    """Immediately trigger a playlist poll (non-blocking, runs in scheduler thread)."""
    from ..scheduler import scheduler
    scheduler.add_job(poll_playlist, id="poll_immediate", replace_existing=True)
    return {"triggered": True}
