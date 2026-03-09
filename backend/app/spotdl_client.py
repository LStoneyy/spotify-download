from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Optional

from spotipy import Spotify


@dataclass
class PlaylistTrack:
    spotify_id: str
    title: str
    artist: Optional[str]
    album: Optional[str]
    duration_ms: Optional[int] = None


@dataclass
class PlaylistInfo:
    spotify_id: str
    name: str
    tracks: list[PlaylistTrack]


def extract_playlist_id(url: str) -> Optional[str]:
    patterns = [
        r"spotify\.com/playlist/([a-zA-Z0-9]+)",
        r"spotify:playlist:([a-zA-Z0-9]+)",
        r"^([a-zA-Z0-9]{22})$",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def fetch_playlist_info(sp: Spotify, url: str) -> PlaylistInfo:
    playlist_id = extract_playlist_id(url)
    if not playlist_id:
        raise ValueError(f"Invalid Spotify playlist URL: {url}")
    
    playlist = sp.playlist(playlist_id)
    playlist_name = playlist.get("name", "Unknown Playlist")
    
    tracks = []
    offset = 0
    limit = 100
    
    while True:
        results = sp.playlist_items(
            playlist_id,
            offset=offset,
            limit=limit
        )
        
        for item in results.get("items", []):
            track = item.get("track") or item.get("item")
            if not track or not track.get("id"):
                continue
            
            artists = track.get("artists", [])
            artist_names = [a.get("name") for a in artists if a.get("name")]
            
            playlist_track = PlaylistTrack(
                spotify_id=track["id"],
                title=track.get("name", "Unknown"),
                artist=", ".join(artist_names) if artist_names else None,
                album=track.get("album", {}).get("name") if track.get("album") else None,
                duration_ms=track.get("duration_ms"),
            )
            tracks.append(playlist_track)
        
        if not results.get("next"):
            break
        
        offset += limit
    
    return PlaylistInfo(
        spotify_id=playlist_id,
        name=playlist_name,
        tracks=tracks,
    )


def sync_playlist(sp: Spotify, url: str, existing_spotify_ids: set[str]) -> tuple[list[PlaylistTrack], PlaylistInfo]:
    info = fetch_playlist_info(sp, url)
    new_tracks = [t for t in info.tracks if t.spotify_id and t.spotify_id not in existing_spotify_ids]
    return new_tracks, info
