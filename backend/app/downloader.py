from __future__ import annotations

import os
import re
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


def _ydl_search_opts(n: int = 5) -> dict:
    """Options for search — no player_client override, default extractor works fine."""
    return {
        **_common_opts(),
        "extract_flat": True,
        "default_search": "ytsearch",
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


# ---------------------------------------------------------------------------
# Token-based result scoring
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> set[str]:
    """Lowercase alphanumeric tokens from a string, filtering trivial stopwords."""
    _STOPWORDS = {"a", "an", "the", "and", "or", "of", "in", "on", "at", "to",
                  "for", "is", "my", "i", "by", "ft", "feat", "official", "video",
                  "audio", "lyrics", "hd", "4k"}
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 1 and w not in _STOPWORDS}


def _score_entry(entry: dict, required: set[str]) -> float:
    """
    Return what fraction of required tokens appear somewhere across
    video title + channel/uploader name.  1.0 = perfect match.
    """
    if not required:
        return 1.0
    video_title = entry.get("title") or ""
    channel = entry.get("channel") or entry.get("uploader") or ""
    haystack = _tokenize(f"{video_title} {channel}")
    matched = required & haystack
    return len(matched) / len(required)


def _entry_url(entry: dict) -> Optional[str]:
    return entry.get("url") or (
        f"https://www.youtube.com/watch?v={entry['id']}" if entry.get("id") else None
    )


def search_youtube(query: str, required_tokens: Optional[set[str]] = None) -> Optional[str]:
    """
    Search YouTube and return the best-matching URL.

    Fetches up to 5 candidates and scores each by how many of the
    *required_tokens* (artist + title words) appear in the combined
    video title + channel name.  Falls back to the top result if nothing
    reaches a perfect score.
    """
    n = 5
    try:
        with yt_dlp.YoutubeDL(_ydl_search_opts()) as ydl:
            info = ydl.extract_info(f"ytsearch{n}:{query}", download=False)
        if not info or not info.get("entries"):
            print(f"[search] No entries returned for query: {query}", flush=True)
            return None

        entries = [e for e in info["entries"] if e]
        if not entries:
            return None

        if not required_tokens:
            # No scoring context — just return the top result
            return _entry_url(entries[0])

        # Score all candidates; pick the best
        scored = [(e, _score_entry(e, required_tokens)) for e in entries]
        scored.sort(key=lambda x: x[1], reverse=True)
        best_entry, best_score = scored[0]

        # Log what we found for debugging
        for e, s in scored[:3]:
            ch = e.get("channel") or e.get("uploader") or "?"
            print(f"[search]   score={s:.2f} channel={ch!r} title={e.get('title')!r}", flush=True)

        # Accept if all required tokens matched; otherwise still use the top result
        # (the fallback chain in _search_with_fallbacks will try simpler queries next)
        if best_score == 1.0:
            print(f"[search] Perfect match (score=1.0): {best_entry.get('title')!r}", flush=True)
            return _entry_url(best_entry)
        elif best_score >= 0.75:
            print(f"[search] Partial match (score={best_score:.2f}): {best_entry.get('title')!r}", flush=True)
            return _entry_url(best_entry)
        else:
            print(f"[search] Best score only {best_score:.2f} — no confident match for query: {query}", flush=True)
            return None

    except Exception as exc:
        print(f"[search] Exception for query '{query}': {exc}", flush=True)
        return None


def _search_with_fallbacks(title: str, artist: str) -> Optional[str]:
    """
    Try progressively simpler search queries, using token scoring to pick
    the best result from each batch of candidates.
    """
    required = _tokenize(f"{artist} {title}")

    queries = []
    if artist:
        queries.append(f"{artist} - {title}")
        queries.append(f"{artist} {title}")
    else:
        queries.append(title)

    for i, q in enumerate(queries):
        print(f"[search] Trying query: {q!r} (required tokens: {required})", flush=True)
        url = search_youtube(q, required_tokens=required)
        if url:
            return url
        if i < len(queries) - 1:
            time.sleep(random.uniform(2.0, 4.0))

    # Last resort: relaxed search with only title tokens, no score filter
    if artist:
        print(f"[search] Falling back to title-only search: {title!r}", flush=True)
        url = search_youtube(title, required_tokens=_tokenize(title))
        if url:
            return url

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
