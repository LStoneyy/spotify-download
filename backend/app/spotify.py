from __future__ import annotations

import json
import os
import re
import time
import urllib.parse
from typing import Optional

import requests

_SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
_SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
_SCOPES = "playlist-read-private playlist-read-collaborative"

_AUTH_PATH = os.environ.get("AUTH_PATH", "/data/spotify_auth.json")

# Fallback Client Credentials cache (used when no OAuth token stored)
_cc_cache: dict = {"token": None, "expires_at": 0.0}

# Web-player token cache (derived from sp_dc cookie)
_wp_cache: dict = {"token": None, "expires_at": 0.0}

_WP_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


# ---------------------------------------------------------------------------
# OAuth token file helpers
# ---------------------------------------------------------------------------

def load_auth() -> Optional[dict]:
    try:
        if os.path.isfile(_AUTH_PATH):
            with open(_AUTH_PATH) as f:
                return json.load(f)
    except Exception:
        pass
    return None


def save_auth(data: dict) -> None:
    os.makedirs(os.path.dirname(_AUTH_PATH) or ".", exist_ok=True)
    with open(_AUTH_PATH, "w") as f:
        json.dump(data, f)


def clear_auth() -> None:
    try:
        os.remove(_AUTH_PATH)
    except FileNotFoundError:
        pass


def is_connected() -> bool:
    return load_auth() is not None


# ---------------------------------------------------------------------------
# Web-player token (sp_dc cookie) — bypasses developer API quota restrictions
# ---------------------------------------------------------------------------

def get_webplayer_token(sp_dc: str) -> str:
    """
    Exchange an sp_dc Spotify session cookie for a web-player access token.
    This token is NOT a developer-API token and is NOT subject to Extended
    Quota Mode restrictions — it is the same token the browser uses.

    Obtain sp_dc once from your browser:
      DevTools → Application → Storage → Cookies → open.spotify.com → sp_dc
    """
    now = time.time()
    if _wp_cache["token"] and now < _wp_cache["expires_at"] - 60:
        return _wp_cache["token"]

    # Step 1: get a client-token (needed as header for the access-token request)
    ct_resp = requests.post(
        "https://clienttoken.spotify.com/v1/clienttoken",
        json={
            "client_data": {
                "client_version": "1.2.46.25.g7f189073",
                "client_id": "d8a5ed958d274c2e8ee717e6a4b0971d",  # web player client id
                "js_sdk_data": {
                    "device_brand": "unknown",
                    "device_model": "desktop",
                    "os": "Windows",
                    "os_version": "NT 10.0",
                    "device_id": "",
                    "device_type": "computer",
                },
            }
        },
        headers={"Accept": "application/json"},
        timeout=10,
    )
    ct_resp.raise_for_status()
    client_token = ct_resp.json().get("granted_token", {}).get("token", "")

    # Step 2: exchange sp_dc + client-token for an access token
    at_resp = requests.get(
        "https://open.spotify.com/get_access_token",
        params={"reason": "transport", "productType": "web_player"},
        headers={
            "User-Agent": _WP_UA,
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "client-token": client_token,
            "Referer": "https://open.spotify.com/",
            "Origin": "https://open.spotify.com",
        },
        cookies={"sp_dc": sp_dc},
        timeout=10,
    )
    at_resp.raise_for_status()
    data = at_resp.json()
    token = data.get("accessToken")
    if not token:
        raise ValueError(f"No accessToken in web-player response: {data}")
    # expires_at is stored as milliseconds timestamp
    exp_ms = data.get("accessTokenExpirationTimestampMs", 0)
    _wp_cache["token"] = token
    _wp_cache["expires_at"] = exp_ms / 1000 if exp_ms else now + 3600
    return token


# ---------------------------------------------------------------------------
# OAuth flow helpers
# ---------------------------------------------------------------------------

def get_auth_url(client_id: str, redirect_uri: str) -> str:
    params = {
        "response_type": "code",
        "client_id": client_id,
        "scope": _SCOPES,
        "redirect_uri": redirect_uri,
    }
    return f"{_SPOTIFY_AUTH_URL}?{urllib.parse.urlencode(params)}"


def exchange_code(client_id: str, client_secret: str, code: str, redirect_uri: str) -> dict:
    """Exchange an authorization code for access + refresh tokens."""
    resp = requests.post(
        _SPOTIFY_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        },
        auth=(client_id, client_secret),
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    auth = {
        "access_token": data["access_token"],
        "refresh_token": data.get("refresh_token"),
        "expires_at": time.time() + data["expires_in"],
    }
    save_auth(auth)
    return auth


def _refresh_oauth_token(client_id: str, client_secret: str, refresh_token: str) -> dict:
    resp = requests.post(
        _SPOTIFY_TOKEN_URL,
        data={"grant_type": "refresh_token", "refresh_token": refresh_token},
        auth=(client_id, client_secret),
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    auth = load_auth() or {}
    auth["access_token"] = data["access_token"]
    auth["expires_at"] = time.time() + data["expires_in"]
    if "refresh_token" in data:  # Spotify sometimes rotates it
        auth["refresh_token"] = data["refresh_token"]
    save_auth(auth)
    return auth


# ---------------------------------------------------------------------------
# Token getter — OAuth preferred, Client Credentials as fallback
# ---------------------------------------------------------------------------

def get_token(client_id: str, client_secret: str) -> str:
    """
    Return a valid Spotify access token.
    - Prefers stored OAuth user token (needed for playlist track access).
    - Falls back to Client Credentials if no OAuth token is stored.
    """
    auth = load_auth()
    if auth:
        if time.time() >= auth.get("expires_at", 0) - 30:
            auth = _refresh_oauth_token(client_id, client_secret, auth["refresh_token"])
        return auth["access_token"]

    # Fallback: Client Credentials (will 403 on playlist tracks in most cases)
    now = time.time()
    if _cc_cache["token"] and now < _cc_cache["expires_at"] - 30:
        return _cc_cache["token"]
    resp = requests.post(
        _SPOTIFY_TOKEN_URL,
        data={"grant_type": "client_credentials"},
        auth=(client_id, client_secret),
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    _cc_cache["token"] = data["access_token"]
    _cc_cache["expires_at"] = now + data["expires_in"]
    return _cc_cache["token"]


# ---------------------------------------------------------------------------
# Playlist helpers
# ---------------------------------------------------------------------------

def _playlist_id_from_url(url_or_id: str) -> str:
    match = re.search(r"playlist/([A-Za-z0-9]+)", url_or_id)
    if match:
        return match.group(1)
    return url_or_id.strip()


def get_playlist_tracks(playlist_url_or_id: str, token: str) -> list[dict]:
    playlist_id = _playlist_id_from_url(playlist_url_or_id)
    url: Optional[str] = (
        f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?limit=100"
    )
    headers = {"Authorization": f"Bearer {token}"}
    tracks: list[dict] = []

    while url:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 403:
            if not is_connected():
                raise Exception(
                    "403 Forbidden — Spotify requires account login to read playlist tracks. "
                    'Go to Settings and click "Connect Spotify Account".'
                )
            else:
                raise Exception(
                    "403 Forbidden from Spotify even with a connected account. "
                    "Since November 2024, Spotify restricts the playlist tracks endpoint for apps "
                    "in Development Mode. You need to apply for 'Extended Quota Mode' at "
                    "https://developer.spotify.com/dashboard → your app → Settings → Request extended access. "
                    "In the meantime, export your playlist via https://exportify.net and use "
                    '"Import CSV" in Settings to queue tracks for download.'
                )
        resp.raise_for_status()
        data = resp.json()

        for item in data.get("items", []):
            track = item.get("track")
            if not track:
                continue
            artists = track.get("artists", [])
            tracks.append(
                {
                    "spotify_id": track.get("id"),
                    "title": track.get("name", ""),
                    "artist": artists[0]["name"] if artists else None,
                    "album": (track.get("album") or {}).get("name"),
                }
            )
        url = data.get("next")

    return tracks
