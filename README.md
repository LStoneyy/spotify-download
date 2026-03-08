# Spotify Playlist Downloader

A self-hosted Docker Compose service that downloads music as MP3s into your
music directory. A React web UI at **http://localhost:6767** lets you request
songs manually, import Spotify playlists via CSV, and configure all settings.

> **Note:** Spotify's November 2024 API policy blocks direct playlist access
> for Development Mode apps — even with a valid OAuth token — and their CDN
> blocks the web-player token endpoint from server/Docker IPs. Direct Spotify
> integration has been removed. Use CSV import (see below) to queue playlists.

## Features

- YouTube search with token-based scoring and smart fallbacks
- Rate-limit–safe downloads: configurable sleep between tracks, exponential backoff on 429s
- Uses the YouTube `tv` client (no PO Token required)
- Optional `cookies.txt` support for improved resilience
- ID3 tag writing (title, artist, album)
- Responsive web UI — works great on mobile and desktop
- Manual song request via the web UI
- CSV playlist import (Exportify format or plain `Artist - Title` lists)
- Configurable file naming templates with live preview
- De-duplication by Spotify ID and by title + artist
- All state persisted in SQLite (survives restarts)

## Requirements

- Docker + Docker Compose

## Setup

### 1. Clone

```bash
git clone https://github.com/LStoneyy/spotify-download.git
cd spotify-download
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and set your music folder:

```env
MUSIC_DIR=/absolute/path/to/your/music/folder
```

### 3. Start

```bash
docker compose up --build -d
```

Open **http://localhost:6767** in your browser.

### 4. Queue tracks

**Option A — Manual request:** Go to **Requests**, type any song name or
`Artist – Title` and hit Enter. It's queued immediately.

**Option B — CSV import:** Export your Spotify playlist with
[Exportify](https://exportify.net), then go to **Settings → Import Playlist CSV**
and upload the file. All tracks are queued and deduplicated automatically.

Downloads start within 15 seconds and run one at a time in the background.

## CSV import formats

| Format | How to obtain |
|--------|---------------|
| **Exportify CSV** (`Spotify ID`, `Track Name`, `Artist Name(s)`, `Album Name`) | [exportify.net](https://exportify.net) |
| Any CSV with `Track Name` / `Artist Name` columns | Any playlist export tool |
| Plain `Artist - Title` per line (no header) | Hand-crafted or text export |

Duplicate tracks (matched by Spotify ID or title + artist) are skipped automatically.

## Web UI

| Page | Description |
|------|-------------|
| **Dashboard** | Live download history, queue stats, active download indicator, status filter |
| **Requests** | Request any song by name or `Artist – Title` format |
| **Settings** | Quality, sleep delay, file naming, CSV import, YouTube cookies hint |

## File naming templates

| Template | Example output |
|----------|---------------|
| `{artist} - {title}` *(default)* | `The Weeknd - Blinding Lights.mp3` |
| `{title}` | `Blinding Lights.mp3` |
| `{album}/{artist} - {title}` | `After Hours/The Weeknd - Blinding Lights.mp3` |

## Optional: YouTube cookies

Mount a `cookies.txt` (Netscape format) to improve download reliability on
rate-limited IPs.

How to export:
1. Install the **Get cookies.txt LOCALLY** extension in Chrome/Firefox
2. Go to [youtube.com](https://www.youtube.com) while logged in
3. Click the extension icon and export `cookies.txt`
4. Set `COOKIES_PATH` in your `.env`:

```env
COOKIES_PATH=/absolute/path/to/cookies.txt
```

Or add it manually under `backend → volumes` in `docker-compose.yml`:

```yaml
- /path/to/cookies.txt:/data/cookies.txt
```

## Volume layout

| Container path | Description |
|----------------|-------------|
| `/music` | Your host music folder (`MUSIC_DIR`) |
| `/data/db.sqlite` | SQLite database (named volume `app_data`) |
| `/data/cookies.txt` | Optional YouTube cookies file |

## Buy me a coffee

If you appreciate my work!  
[Paypal.me](https://www.paypal.me/dcmbrbeats)

## License

This project is for personal use and educational purposes only. Do not use it to infringe on copyright laws.
