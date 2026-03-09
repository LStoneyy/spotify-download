from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from spotipy.oauth2 import SpotifyOAuth as SpotipyOAuth
from spotipy import Spotify

from ..database import SpotifyOAuth as SpotifyOAuthModel, get_session

router = APIRouter(tags=["auth"])

CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID", "f8a606e5583643beaa27ce62c48e3fc1")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "f6f4c8f73f0649939286cf417c811607")
REDIRECT_URI = os.environ.get("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:6767/api/auth/callback")

SCOPES = "playlist-read-private"

_oauth_manager: Optional[SpotipyOAuth] = None


def get_oauth_manager() -> SpotipyOAuth:
    global _oauth_manager
    if _oauth_manager is None:
        _oauth_manager = SpotipyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=SCOPES,
            cache_path=None,
            requests_timeout=10,
        )
    return _oauth_manager


class AuthStatus(BaseModel):
    authenticated: bool
    expires_at: Optional[int] = None


class TokenInfo(BaseModel):
    access_token: str
    refresh_token: str
    expires_at: int


def get_valid_token(session: Session) -> Optional[str]:
    oauth_record = session.exec(select(SpotifyOAuthModel)).first()
    if not oauth_record:
        return None
    
    now = int(time.time())
    if oauth_record.token_expires_at < now + 60:
        oauth_manager = get_oauth_manager()
        try:
            token_info = oauth_manager.refresh_access_token(oauth_record.refresh_token)
            oauth_record.access_token = token_info["access_token"]
            oauth_record.refresh_token = token_info.get("refresh_token", oauth_record.refresh_token)
            oauth_record.token_expires_at = token_info["expires_at"]
            oauth_record.updated_at = datetime.now(timezone.utc)
            session.add(oauth_record)
            session.commit()
        except Exception as e:
            print(f"[auth] Token refresh failed: {e}", flush=True)
            session.delete(oauth_record)
            session.commit()
            return None
    
    return oauth_record.access_token


def get_spotify_client(session: Session = Depends(get_session)) -> Optional[Spotify]:
    token = get_valid_token(session)
    if not token:
        return None
    return Spotify(auth=token)


@router.get("/auth/status", response_model=AuthStatus)
def auth_status(session: Session = Depends(get_session)):
    oauth_record = session.exec(select(SpotifyOAuthModel)).first()
    if not oauth_record:
        return AuthStatus(authenticated=False)
    
    now = int(time.time())
    if oauth_record.token_expires_at < now + 60:
        return AuthStatus(authenticated=False, expires_at=oauth_record.token_expires_at)
    
    return AuthStatus(authenticated=True, expires_at=oauth_record.token_expires_at)


@router.get("/auth/login")
def login():
    oauth_manager = get_oauth_manager()
    auth_url = oauth_manager.get_authorize_url()
    return RedirectResponse(url=auth_url)


@router.get("/auth/callback")
def callback(code: str, session: Session = Depends(get_session)):
    oauth_manager = get_oauth_manager()
    
    try:
        token_info = oauth_manager.get_access_token(code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get access token: {e}")
    
    existing = session.exec(select(SpotifyOAuthModel)).first()
    if existing:
        session.delete(existing)
    
    oauth_record = SpotifyOAuthModel(
        access_token=token_info["access_token"],
        refresh_token=token_info["refresh_token"],
        token_expires_at=token_info["expires_at"],
    )
    session.add(oauth_record)
    session.commit()
    
    return RedirectResponse(url="/settings")


@router.post("/auth/logout")
def logout(session: Session = Depends(get_session)):
    oauth_record = session.exec(select(SpotifyOAuthModel)).first()
    if oauth_record:
        session.delete(oauth_record)
        session.commit()
    return {"ok": True}
