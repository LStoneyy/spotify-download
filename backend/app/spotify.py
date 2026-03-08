from __future__ import annotations

import re
import time
from typing import Optional

import requests

_token_cache: dict = {"token": None, "expires_at": 0.0}


def get_token(client_id: str, client_secret: str) -> str:
    now = time.time()
    if _token_cache["token"] and now < _token_cache["expires_at"] - 30:
        return _token_cache["token"]

    resp = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(client_id, client_secret),
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    _token_cache["token"] = data["access_token"]
    _token_cache["expires_at"] = now + data["expires_in"]
    return _token_cache["token"]


def _playlist_id_from_url(url_or_id: str) -> str:
    """Accept a full Spotify URL or bare playlist ID."""
    match = re.search(r"playlist/([A-Za-z0-9]+)", url_or_id)
    if match:
        return match.group(1)
    return url_or_id.strip()


def get_playlist_tracks(playlist_url_or_id: str, token: str) -> list[dict]:
    playlist_id = _playlist_id_from_url(playlist_url_or_id)
    url: Optional[str] = (
        f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        "?fields=next,items(track(id,name,album(name),artists(name)))&limit=100"
    )
    headers = {"Authorization": f"Bearer {token}"}
    tracks: list[dict] = []

    while url:
        resp = requests.get(url, headers=headers, timeout=15)
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
