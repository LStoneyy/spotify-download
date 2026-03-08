from __future__ import annotations

import os
import threading
from datetime import datetime, timezone
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from sqlmodel import Session, select

from .database import Settings, Track, engine, get_settings
from .downloader import download_track

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

_download_lock = threading.Lock()
_currently_downloading: Optional[dict] = None  # {track_id, title, artist}

scheduler = BackgroundScheduler(timezone="UTC")


def get_current_state() -> dict:
    return {
        "currently_downloading": _currently_downloading,
    }


# ---------------------------------------------------------------------------
# Download worker — drains queue one track at a time
# ---------------------------------------------------------------------------

def download_worker() -> None:
    global _currently_downloading

    if not _download_lock.acquire(blocking=False):
        return  # another download is already in progress

    try:
        with Session(engine) as session:
            track = session.exec(
                select(Track).where(Track.status == "queued").order_by(Track.requested_at)
            ).first()

            if not track:
                return

            settings = get_settings(session)
            quality = settings.quality
            template = settings.file_template
            sleep_sec = settings.sleep_between_downloads
            max_retries = settings.max_retries
            output_dir = os.environ.get("OUTPUT_DIR", "/music")

            track.status = "downloading"
            session.add(track)
            session.commit()
            session.refresh(track)

            track_id = track.id
            track_title = track.title
            track_artist = track.artist
            track_album = track.album

        _currently_downloading = {
            "track_id": track_id,
            "title": track_title,
            "artist": track_artist,
        }

        label = f"{track_artist} - {track_title}" if track_artist else track_title
        print(f"[downloader] Searching: {label}", flush=True)

        success, file_path, error = download_track(
            title=track_title,
            artist=track_artist,
            album=track_album,
            output_dir=output_dir,
            quality=quality,
            template=template,
            sleep_sec=sleep_sec,
            max_retries=max_retries,
            log_fn=lambda msg: print(f"[downloader] {msg}", flush=True),
        )

        with Session(engine) as session:
            t = session.get(Track, track_id)
            if t:
                if success:
                    t.status = "done"
                    t.file_path = file_path
                    t.downloaded_at = datetime.now(timezone.utc)
                elif file_path:
                    # file_path returned but success=False means already existed (skipped)
                    t.status = "skipped"
                    t.file_path = file_path
                else:
                    t.status = "failed"
                    t.error_msg = error
                    print(f"[downloader] FAILED: {error}", flush=True)
                session.add(t)
                session.commit()

    finally:
        _currently_downloading = None
        _download_lock.release()


def start_scheduler() -> None:
    scheduler.add_job(
        download_worker,
        trigger="interval",
        seconds=15,
        id="worker",
        replace_existing=True,
    )
    scheduler.start()
    print("[scheduler] Started download worker.", flush=True)


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
