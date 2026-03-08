from __future__ import annotations

import os
import time
import random
from datetime import datetime
from typing import Optional

import yt_dlp
import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

_COOKIES_PATH = "/data/cookies.txt"

# ---------------------------------------------------------------------------
# Filename helpers
# ---------------------------------------------------------------------------

_ILLEGAL = str.maketrans(
    {
        "/": "_",
        "\\": "_",
        ":": "-",
        "?": "",
        "*": "",
        '"': "'",
        "<": "(",
        ">": ")",
        "|": "-",
    }
)


def sanitize_filename(template: str, title: str, artist: str, album: str) -> str:
    """Apply user template then strip filesystem-illegal characters."""
    name = (
        template.replace("{title}", title or "")
        .replace("{artist}", artist or "Unknown Artist")
        .replace("{album}", album or "Unknown Album")
    )
    return name.strip().translate(_ILLEGAL)


# ---------------------------------------------------------------------------
# YouTube search
# ---------------------------------------------------------------------------

def _common_opts() -> dict:
    """Options shared by both search and download."""
    opts = {
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "geo_bypass": True,
        "http_headers": {
            "User-Agent": _UA,
            "Accept-Language": "en-US,en;q=0.9",
        },
    }
    # Pass cookies only if the file exists AND has content (not the empty placeholder)
    if os.path.isfile(_COOKIES_PATH) and os.path.getsize(_COOKIES_PATH) > 0:
        opts["cookiefile"] = _COOKIES_PATH
    return opts


def _ydl_search_opts() -> dict:
    """Options for search — no player_client override, default extractor works fine."""
    return {
        **_common_opts(),
        "extract_flat": True,
        "default_search": "ytsearch",
        "max_downloads": 1,
        "ignoreerrors": True,
    }


def _ydl_download_opts(output_base: str, quality: str, sleep_sec: int, max_retries: int) -> dict:
    """Options for actual audio download — uses android_vr to bypass bot checks."""
    return {
        **_common_opts(),
        "format": "bestaudio/best",
        "outtmpl": output_base,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": quality,
            }
        ],
        "noplaylist": True,
        "noprogress": True,
        # android_vr bypasses YouTube's bot-check without needing cookies or a PO Token.
        # tv is kept as fallback. Separate from search opts — android_vr breaks flat search.
        "extractor_args": {
            "youtube": {
                "player_client": ["android_vr", "tv"],
                "skip": ["hls", "dash"],
            }
        },
        "sleep_interval": sleep_sec,
        "max_sleep_interval": sleep_sec + 5,
        "sleep_interval_requests": 1,
        "retries": max_retries,
        "retry_sleep_functions": {
            "http": lambda n: min(10 * (2 ** (n - 1)), 120),
        },
        "concurrent_fragment_downloads": 1,
    }


def search_youtube(query: str) -> Optional[str]:
    """Return the best YouTube URL for *query*, or None on failure."""
    try:
        with yt_dlp.YoutubeDL(_ydl_search_opts()) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
        if not info or not info.get("entries"):
            return None
        entry = info["entries"][0]
        if not entry:
            return None
        return f"https://www.youtube.com/watch?v={entry['id']}"
    except Exception:
        return None


def _search_with_fallbacks(title: str, artist: str) -> Optional[str]:
    """Try three progressively simpler search queries."""
    queries = []
    if artist:
        queries.append(f"{artist} - {title} official audio")
        queries.append(f"{artist} {title}")
        first_word = title.split()[0] if title.split() else title
        queries.append(f"{artist} {first_word}")
    else:
        queries.append(f"{title} official audio")
        queries.append(title)

    for i, q in enumerate(queries):
        url = search_youtube(q)
        if url:
            return url
        if i < len(queries) - 1:
            time.sleep(random.uniform(2.0, 4.0))
    return None


# ---------------------------------------------------------------------------
# MP3 metadata
# ---------------------------------------------------------------------------
def _set_metadata(path: str, title: str, artist: Optional[str], album: Optional[str]) -> None:
    """Write ID3 tags using EasyID3 (single pass, no redundant double-write)."""
    try:
        try:
            audio = EasyID3(path)
        except ID3NoHeaderError:
            audio = mutagen.File(path, easy=True)
            if audio is None:
                return
            audio.add_tags()
        audio["title"] = title
        if artist:
            audio["artist"] = artist
        if album:
            audio["album"] = album
        audio.save()
    except Exception:
        pass  # Metadata failure is non-fatal


# ---------------------------------------------------------------------------
# Core download
# ---------------------------------------------------------------------------

def download_track(
    *,
    title: str,
    artist: Optional[str],
    album: Optional[str],
    output_dir: str,
    quality: str = "320",
    template: str = "{artist} - {title}",
    sleep_sec: int = 7,
    max_retries: int = 3,
    log_fn=None,
) -> tuple[bool, Optional[str], Optional[str]]:
    """
    Download a single track.

    Returns (success, file_path, error_message).
    """

    def _log(msg: str) -> None:
        if log_fn:
            log_fn(msg)

    os.makedirs(output_dir, exist_ok=True)

    file_name = sanitize_filename(template, title or "", artist or "", album or "")
    if not file_name:
        return False, None, "Empty filename after sanitization"

    final_path = os.path.join(output_dir, f"{file_name}.mp3")
    if os.path.exists(final_path):
        _log(f"Already exists: {file_name}")
        return False, final_path, None  # skipped – file already present

    # Find the YouTube URL
    youtube_url = _search_with_fallbacks(title or "", artist or "")
    if not youtube_url:
        search_label = f"{artist} - {title}" if artist else title
        return False, None, f"No YouTube result found for: {search_label}"

    # Build a temp path using os.splitext to avoid the .mp3-in-path bug
    base_temp = os.path.join(output_dir, f"_tmp_{file_name}")
    base_no_ext, _ = os.path.splitext(base_temp + ".mp3")  # strips nothing, but future-proof

    ydl_opts = _ydl_download_opts(base_no_ext, quality, sleep_sec, max_retries)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
    except Exception as exc:
        # Clean up any partial temp files
        for ext in (".mp3", ".webm", ".m4a", ".opus", ".part"):
            p = base_no_ext + ext
            if os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass
        return False, None, str(exc)

    # Locate the downloaded file (yt-dlp appends its own extension)
    downloaded = None
    for ext in (".mp3", ".webm", ".m4a", ".opus"):
        candidate = base_no_ext + ext
        if os.path.exists(candidate):
            downloaded = candidate
            break

    if not downloaded:
        return False, None, "Downloaded file not found after yt-dlp run"

    # Ensure it ends up as .mp3
    if not downloaded.endswith(".mp3"):
        mp3_temp = base_no_ext + ".mp3"
        os.rename(downloaded, mp3_temp)
        downloaded = mp3_temp

    _set_metadata(downloaded, title or "", artist, album)

    os.rename(downloaded, final_path)
    _log(f"Downloaded: {file_name}")
    return True, final_path, None
