from __future__ import annotations

import os
import threading
from datetime import datetime, timezone
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from sqlmodel import Session, select

from .database import Settings, Track, engine, get_settings
from .downloader import download_track
from .spotify import get_playlist_tracks, get_token, get_webplayer_token

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

_download_lock = threading.Lock()
_currently_downloading: Optional[dict] = None  # {track_id, title, artist}
_last_poll: Optional[datetime] = None
_next_poll: Optional[datetime] = None

scheduler = BackgroundScheduler(timezone="UTC")


def get_current_state() -> dict:
    return {
        "currently_downloading": _currently_downloading,
        "last_poll": _last_poll.isoformat() if _last_poll else None,
        "next_poll": _next_poll.isoformat() if _next_poll else None,
    }


# ---------------------------------------------------------------------------
# Poll job — runs on an interval, syncs playlist → DB
# ---------------------------------------------------------------------------

def poll_playlist() -> dict:
    """Sync playlist → DB. Returns a result dict describing what happened."""
    global _last_poll, _next_poll

    with Session(engine) as session:
        settings = get_settings(session)
        playlist_url = settings.playlist_url
        poll_minutes = settings.poll_interval_minutes
        sp_dc = (settings.sp_dc or "").strip()

    _last_poll = datetime.now(timezone.utc)

    try:
        job = scheduler.get_job("poll")
        if job and job.next_run_time:
            _next_poll = job.next_run_time
    except Exception:
        pass

    if not playlist_url:
        return {"ok": False, "error": "No playlist URL configured. Set it in Settings first."}

    # ── Choose best available token ─────────────────────────────────────────
    token: Optional[str] = None

    if sp_dc:
        try:
            token = get_webplayer_token(sp_dc)
            print("[scheduler] Using sp_dc web-player token (bypasses quota limits)", flush=True)
        except Exception as e:
            print(f"[scheduler] sp_dc token failed: {e} — falling back to developer API", flush=True)

    if token is None:
        # Fall back to developer API (OAuth or Client Credentials)
        client_id = os.environ.get("SPOTIFY_CLIENT_ID", "")
        client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET", "")
        if not client_id or not client_secret:
            return {"ok": False, "error": "Spotify credentials missing. Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in your .env, or configure the sp_dc cookie in Settings."}
        try:
            token = get_token(client_id, client_secret)
        except Exception as e:
            return {"ok": False, "error": f"Spotify token error: {e}"}

    try:
        remote_tracks = get_playlist_tracks(playlist_url, token)
    except Exception as exc:
        msg = f"Spotify API error: {exc}"
        print(f"[scheduler] {msg}")
        return {"ok": False, "error": msg}

    total_found = len(remote_tracks)

    with Session(engine) as session:
        # Collect existing spotify_ids AND title+artist pairs to avoid duplicates
        existing_ids: set[str] = set()
        existing_ta: set[tuple[str, str]] = set()  # (lower_title, lower_artist)
        for row in session.exec(select(Track)):
            if row.spotify_id:
                existing_ids.add(row.spotify_id)
            if row.title:
                existing_ta.add((row.title.lower(), (row.artist or "").lower()))

        added = 0
        for t in remote_tracks:
            sid = t.get("spotify_id")
            title = t.get("title", "")
            artist = t.get("artist") or ""

            if sid and sid in existing_ids:
                continue
            if (title.lower(), artist.lower()) in existing_ta:
                continue

            new_track = Track(
                spotify_id=sid,
                title=title,
                artist=artist or None,
                album=t.get("album"),
                status="queued",
                source="playlist",
            )
            session.add(new_track)
            if sid:
                existing_ids.add(sid)
            existing_ta.add((title.lower(), artist.lower()))
            added += 1

        session.commit()
        print(f"[scheduler] Playlist sync: {total_found} tracks found, {added} new queued.")

    # Reschedule if interval changed
    _reschedule_poll(poll_minutes)

    return {"ok": True, "total_found": total_found, "added": added}


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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reschedule_poll(minutes: int) -> None:
    try:
        job = scheduler.get_job("poll")
        if job:
            # Only reschedule if the interval actually changed
            current_interval = job.trigger.interval.total_seconds() / 60
            if abs(current_interval - minutes) > 0.5:
                scheduler.reschedule_job(
                    "poll",
                    trigger="interval",
                    minutes=minutes,
                )
    except Exception:
        pass


def start_scheduler() -> None:
    with Session(engine) as session:
        settings = get_settings(session)
        poll_minutes = settings.poll_interval_minutes

    scheduler.add_job(
        poll_playlist,
        trigger="interval",
        minutes=poll_minutes,
        id="poll",
        replace_existing=True,
    )
    scheduler.add_job(
        download_worker,
        trigger="interval",
        seconds=15,
        id="worker",
        replace_existing=True,
    )
    scheduler.start()
    print("[scheduler] Started. Poll every", poll_minutes, "min.")


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
