from __future__ import annotations

import os

from fastapi import APIRouter
from fastapi.responses import JSONResponse, RedirectResponse

from ..spotify import clear_auth, exchange_code, get_auth_url, load_auth

router = APIRouter()


def _redirect_uri() -> str:
    host = os.environ.get("PUBLIC_HOST", "http://127.0.0.1:6767")
    return f"{host.rstrip('/')}/api/spotify/callback"


@router.get("/spotify/auth")
def spotify_auth():
    """Redirect the browser to Spotify's OAuth consent page."""
    client_id = os.environ.get("SPOTIFY_CLIENT_ID", "")
    if not client_id:
        return JSONResponse({"error": "SPOTIFY_CLIENT_ID not set"}, status_code=500)
    url = get_auth_url(client_id, _redirect_uri())
    return RedirectResponse(url)


@router.get("/spotify/callback")
def spotify_callback(code: str = "", error: str = ""):
    """Spotify redirects here after the user authorises (or denies) access."""
    client_id = os.environ.get("SPOTIFY_CLIENT_ID", "")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET", "")

    if error:
        return RedirectResponse(f"/settings?spotify_error={error}")

    if not code:
        return JSONResponse({"error": "No code received"}, status_code=400)

    try:
        exchange_code(client_id, client_secret, code, _redirect_uri())
    except Exception as exc:
        return RedirectResponse(f"/settings?spotify_error={exc}")

    # Redirect back to the UI settings page
    return RedirectResponse("/settings?spotify_connected=1")


@router.get("/spotify/status")
def spotify_status():
    auth = load_auth()
    if not auth:
        return {"connected": False, "expires_at": None}
    return {
        "connected": True,
        "expires_at": auth.get("expires_at"),
    }


@router.delete("/spotify/disconnect")
def spotify_disconnect():
    clear_auth()
    return {"disconnected": True}
