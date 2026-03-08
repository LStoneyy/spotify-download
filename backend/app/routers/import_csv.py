from __future__ import annotations

import csv
import io
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlmodel import Session, or_, select, func

from ..database import Track, get_session

router = APIRouter()

# ---------------------------------------------------------------------------
# CSV column name variants (Exportify + common export tools)
# ---------------------------------------------------------------------------

_TITLE_COLS = ["track name", "title", "song", "name", "track"]
_ARTIST_COLS = ["artist name(s)", "artist names", "artist name", "artist", "artists", "performer"]
_ALBUM_COLS = ["album name", "album", "release"]
_ID_COLS = ["spotify id", "spotify_id", "track id", "track_id", "uri", "id"]


def _find_col(headers: list[str], candidates: list[str]) -> str | None:
    """Return the first header that matches any candidate (case-insensitive)."""
    lower = [h.lower().strip() for h in headers]
    for c in candidates:
        if c in lower:
            return headers[lower.index(c)]
    return None


def _parse_csv(content: str) -> list[dict]:
    """
    Parse CSV content and return a list of dicts with keys: title, artist, album, spotify_id.
    Supports:
      - Exportify format (header row with recognized column names)
      - Simple 2-column format: Title,Artist or Artist,Title
      - One-column "Artist - Title" or "Title" per line (no header)
    """
    lines = content.splitlines()
    if not lines:
        return []

    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    if not rows:
        return []

    headers = rows[0]
    title_col = _find_col(headers, _TITLE_COLS)
    artist_col = _find_col(headers, _ARTIST_COLS)
    album_col = _find_col(headers, _ALBUM_COLS)
    id_col = _find_col(headers, _ID_COLS)

    results = []

    if title_col:
        # Header row present — use named columns
        dict_reader = csv.DictReader(io.StringIO(content))
        for row in dict_reader:
            title = row.get(title_col, "").strip()
            if not title:
                continue
            # Artist may be comma-separated list (Exportify); take the first one
            artist_raw = row.get(artist_col or "", "").strip() if artist_col else None
            artist = artist_raw.split(",")[0].strip() if artist_raw else None
            album = row.get(album_col or "", "").strip() if album_col else None or None
            spotify_id = row.get(id_col or "", "").strip() if id_col else None
            # Exportify stores as "spotify:track:xxxx" — extract just the ID part
            if spotify_id and spotify_id.startswith("spotify:track:"):
                spotify_id = spotify_id.split(":")[-1]
            results.append({
                "title": title,
                "artist": artist or None,
                "album": album or None,
                "spotify_id": spotify_id or None,
            })
    else:
        # No recognised header — treat as headerless
        for row in rows:
            if not row:
                continue
            cell = row[0].strip()
            if not cell:
                continue
            # Try "Artist - Title" convention
            if " - " in cell:
                parts = cell.split(" - ", 1)
                artist, title = parts[0].strip(), parts[1].strip()
            elif len(row) >= 2:
                # Two columns: try Title, Artist
                title = row[0].strip()
                artist = row[1].strip() if row[1].strip() else None
            else:
                title = cell
                artist = None
            if title:
                results.append({
                    "title": title,
                    "artist": artist or None,
                    "album": None,
                    "spotify_id": None,
                })

    return results


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.post("/import/csv")
async def import_csv(
    file: Annotated[UploadFile, File(description="CSV playlist export (Exportify or similar)")],
    session: Session = Depends(get_session),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted.")

    raw = await file.read()
    try:
        content = raw.decode("utf-8-sig")  # utf-8-sig strips BOM (common in Excel exports)
    except UnicodeDecodeError:
        content = raw.decode("latin-1")

    parsed = _parse_csv(content)
    if not parsed:
        raise HTTPException(status_code=400, detail="No tracks found in CSV. Check the file format.")

    imported = 0
    skipped = 0

    for item in parsed:
        title = item["title"]
        artist = item["artist"]
        spotify_id = item["spotify_id"]

        # Check for duplicate by spotify_id (if present) or title+artist
        existing = None
        if spotify_id:
            existing = session.exec(
                select(Track).where(Track.spotify_id == spotify_id)
            ).first()
        if not existing:
            # Case-insensitive title + artist match
            filters = [func.lower(Track.title) == title.lower()]
            if artist:
                filters.append(func.lower(Track.artist) == artist.lower())
            existing = session.exec(select(Track).where(*filters)).first()

        if existing:
            skipped += 1
            continue

        track = Track(
            spotify_id=spotify_id,
            title=title,
            artist=artist,
            album=item["album"],
            status="queued",
            source="playlist",
        )
        session.add(track)
        imported += 1

    session.commit()

    return {
        "ok": True,
        "total": len(parsed),
        "imported": imported,
        "skipped": skipped,
    }
