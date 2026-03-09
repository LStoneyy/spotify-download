from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from ..database import MonitoredPlaylist, Track, engine
from ..spotdl_client import extract_playlist_id, fetch_playlist_info, sync_playlist
from .auth import get_spotify_client, get_valid_token

router = APIRouter(tags=["playlists"])


def get_session():
    with Session(engine) as session:
        yield session


class PlaylistCreate(BaseModel):
    url: str


class PlaylistResponse(BaseModel):
    id: int
    spotify_id: str
    name: Optional[str]
    url: str
    track_count: int
    last_synced_at: Optional[datetime]
    sync_error: Optional[str]
    created_at: datetime


class SyncResult(BaseModel):
    playlist_id: int
    new_tracks: int
    total_tracks: int
    error: Optional[str] = None


@router.get("/playlists", response_model=list[PlaylistResponse])
def list_playlists(session: Session = Depends(get_session)):
    playlists = session.exec(select(MonitoredPlaylist).order_by(MonitoredPlaylist.created_at.desc())).all()
    return playlists


@router.post("/playlists", response_model=PlaylistResponse)
def add_playlist(body: PlaylistCreate, session: Session = Depends(get_session)):
    playlist_id = extract_playlist_id(body.url)
    if not playlist_id:
        raise HTTPException(status_code=400, detail="Invalid Spotify playlist URL")
    
    existing = session.exec(
        select(MonitoredPlaylist).where(MonitoredPlaylist.spotify_id == playlist_id)
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Playlist already monitored")
    
    token = get_valid_token(session)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated with Spotify. Please login first.")
    
    from spotipy import Spotify
    sp = Spotify(auth=token)
    
    try:
        info = fetch_playlist_info(sp, body.url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch playlist: {str(e)}")
    
    playlist = MonitoredPlaylist(
        spotify_id=playlist_id,
        name=info.name,
        url=body.url,
        track_count=len(info.tracks),
        last_synced_at=datetime.now(timezone.utc),
    )
    session.add(playlist)
    
    existing_track_ids = set(
        sid for sid in session.exec(
            select(Track.spotify_id).where(Track.spotify_id.is_not(None))
        ).all()
    )
    
    new_count = 0
    for track in info.tracks:
        if track.spotify_id and track.spotify_id in existing_track_ids:
            continue
        if track.spotify_id:
            existing_track_ids.add(track.spotify_id)
        
        db_track = Track(
            spotify_id=track.spotify_id or None,
            title=track.title,
            artist=track.artist,
            album=track.album,
            status="queued",
            source="playlist",
        )
        session.add(db_track)
        new_count += 1
    
    session.commit()
    session.refresh(playlist)
    print(f"[playlists] Added playlist '{info.name}' with {new_count} new tracks", flush=True)
    return playlist


@router.delete("/playlists/{playlist_id}")
def delete_playlist(playlist_id: int, session: Session = Depends(get_session)):
    playlist = session.get(MonitoredPlaylist, playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    session.delete(playlist)
    session.commit()
    return {"ok": True}


@router.post("/playlists/{playlist_id}/sync", response_model=SyncResult)
def sync_playlist_endpoint(playlist_id: int, session: Session = Depends(get_session)):
    playlist = session.get(MonitoredPlaylist, playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    token = get_valid_token(session)
    if not token:
        return SyncResult(
            playlist_id=playlist_id,
            new_tracks=0,
            total_tracks=0,
            error="Not authenticated with Spotify. Please login first.",
        )
    
    from spotipy import Spotify
    sp = Spotify(auth=token)
    
    existing_track_ids = set(
        sid for sid in session.exec(
            select(Track.spotify_id).where(Track.spotify_id.is_not(None))
        ).all()
    )
    
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
        
        session.add(playlist)
        session.commit()
        
        print(f"[playlists] Synced '{info.name}': {len(new_tracks)} new tracks", flush=True)
        return SyncResult(
            playlist_id=playlist_id,
            new_tracks=len(new_tracks),
            total_tracks=len(info.tracks),
        )
    except Exception as e:
        playlist.sync_error = str(e)
        playlist.last_synced_at = datetime.now(timezone.utc)
        session.add(playlist)
        session.commit()
        return SyncResult(
            playlist_id=playlist_id,
            new_tracks=0,
            total_tracks=0,
            error=str(e),
        )
