from __future__ import annotations

import os
import threading
from datetime import datetime, timezone
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from spotipy import Spotify
from sqlmodel import Session, select

from .database import MonitoredPlaylist, Settings, SpotifyOAuth, Track, engine, get_settings
from .downloader import download_track
from .spotdl_client import sync_playlist

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
    scheduler.add_job(
        playlist_sync_worker,
        trigger="interval",
        hours=1,
        id="playlist_sync",
        replace_existing=True,
    )
    scheduler.start()
    print("[scheduler] Started download worker and playlist sync.", flush=True)


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)


def playlist_sync_worker() -> None:
    with Session(engine) as session:
        oauth_record = session.exec(select(SpotifyOAuth)).first()
        if not oauth_record:
            return
        
        import time
        now = int(time.time())
        if oauth_record.token_expires_at < now + 60:
            from spotipy.oauth2 import SpotifyOAuth as SpotipyOAuth
            import os
            try:
                oauth_manager = SpotipyOAuth(
                    client_id=os.environ.get("SPOTIFY_CLIENT_ID", "f8a606e5583643beaa27ce62c48e3fc1"),
                    client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET", "f6f4c8f73f0649939286cf417c811607"),
                    redirect_uri=os.environ.get("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:6767/api/auth/callback"),
                    scope="playlist-read-private",
                    cache_path=None,
                )
                token_info = oauth_manager.refresh_access_token(oauth_record.refresh_token)
                oauth_record.access_token = token_info["access_token"]
                oauth_record.refresh_token = token_info.get("refresh_token", oauth_record.refresh_token)
                oauth_record.token_expires_at = token_info["expires_at"]
                oauth_record.updated_at = datetime.now(timezone.utc)
                session.add(oauth_record)
                session.commit()
            except Exception as e:
                print(f"[scheduler] Token refresh failed: {e}", flush=True)
                return
        
        sp = Spotify(auth=oauth_record.access_token)
        
        playlists = session.exec(select(MonitoredPlaylist)).all()
        if not playlists:
            return
        
        existing_track_ids = set(
            sid for sid in session.exec(
                select(Track.spotify_id).where(Track.spotify_id.is_not(None))
            ).all()
        )
        
        for playlist in playlists:
            try:
                new_tracks, info = sync_playlist(sp, playlist.url, existing_track_ids)
                playlist.name = info.name
                playlist.track_count = len(info.tracks)
                playlist.last_synced_at = datetime.now(timezone.utc)
                playlist.sync_error = None
                
                for track in new_tracks:
                    db_track = Track(
                        spotify_id=track.spotify_id or None,
                        title=track.title,
                        artist=track.artist,
                        album=track.album,
                        status="queued",
                        source="playlist",
                    )
                    session.add(db_track)
                    if track.spotify_id:
                        existing_track_ids.add(track.spotify_id)
                
                session.add(playlist)
                
                if new_tracks:
                    print(f"[scheduler] Synced '{info.name}': {len(new_tracks)} new tracks", flush=True)
            except Exception as e:
                playlist.sync_error = str(e)
                playlist.last_synced_at = datetime.now(timezone.utc)
                session.add(playlist)
                print(f"[scheduler] Sync failed for '{playlist.name}': {e}", flush=True)
        
        session.commit()
