# Spotify Playlist Downloader

A self-hosted Docker Compose service that monitors a Spotify playlist and
automatically downloads new tracks as MP3s into your music directory.  
A React web UI at **http://localhost:6767** lets you monitor downloads, request
songs manually, and configure all settings.

## Features

- Automatic playlist polling — detects new tracks and queues them
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
- A free [Spotify Developer App](https://developer.spotify.com/dashboard) (Client ID + Secret)
- Your own Spotify account logged in to a browser (to copy the `sp_dc` cookie — see below)

## Setup

### 1. Clone

```bash
git clone https://github.com/LStoneyy/spotify-download.git
cd spotify-download
```

### 2. Create a Spotify Developer App

This is needed so the web UI can authenticate with your account via OAuth.

1. Go to [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
2. Click **Create app**
3. Fill in any name/description
4. Under **Redirect URIs** add: `http://127.0.0.1:6767/api/spotify/callback`
   - `localhost` is **not** allowed — it must be the literal IP `127.0.0.1`
5. Under **Which API/SDKs are you planning to use?** tick **Web API** only
6. Copy your **Client ID** and **Client Secret**

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
MUSIC_DIR=/absolute/path/to/your/music/folder
```

### 4. Start

```bash
docker compose up --build -d
```

Open **http://localhost:6767** in your browser.

### 5. Connect your Spotify account (OAuth)

Go to **Settings** → **Spotify** → **Connect Spotify Account** and log in.  
This stores a refresh token in the container volume and auto-renews it.

> **Note:** Due to a [Spotify API policy change in November 2024](https://community.spotify.com/t5/Spotify-for-Developers/Web-API-Restriction-playlist-tracks-endpoint/td-p/5664283),
> apps in Development Mode are blocked from reading playlist tracks via the developer API —
> even with a valid OAuth token. The fix is the `sp_dc` cookie below.

### 6. Set the sp_dc cookie — required for playlist sync ⚠️

The `sp_dc` cookie is your browser's Spotify session. It uses a **different token flow**
that is not subject to the developer API quota restriction. You extract it once from
your browser and paste it into Settings — no developer approval process needed.

1. Open [open.spotify.com](https://open.spotify.com) and log in
2. Open DevTools (`F12`) → **Application** → **Storage** → **Cookies** → `https://open.spotify.com`
3. Find the cookie named **`sp_dc`** and copy its value (a long string starting with `AQ…`)
4. Go to **Settings** → **Spotify Session Cookie (sp_dc)** → paste the value → **Save**

The cookie typically lasts several months. If syncing stops working, repeat this step — you can see whether it is set in Settings (shows a green "Configured" badge).

### 7. Set the playlist URL and sync

1. Go to **Settings** → paste your Spotify playlist URL → **Save settings**
2. Click **Sync Now** on the Dashboard to trigger the first poll
3. New tracks are downloaded automatically on every poll interval

## Sync priority order

When syncing, the backend tries tokens in this order:

| Priority | Method | Works after Nov 2024 API change? |
|----------|--------|----------------------------------|
| 1 | `sp_dc` cookie → web-player token | ✅ Yes |
| 2 | OAuth user token (developer API) | ❌ No (403 on playlist tracks) |
| 3 | Client Credentials (developer API) | ❌ No (403 on playlist tracks) |

Always configure the `sp_dc` cookie for reliable syncing.

## Alternative: CSV import

If you cannot use the `sp_dc` approach, export your playlist with
[Exportify](https://exportify.net) and upload the CSV in **Settings → Import Playlist CSV**.

Supported CSV formats:
- **Exportify** — columns `Spotify ID`, `Track Name`, `Artist Name(s)`, `Album Name`
- Any CSV with a `Track Name` / `Artist Name` header row
- Headerless `Artist - Title` per line (no header needed)

Duplicate tracks are skipped automatically.

## Web UI

| Page | Description |
|------|-------------|
| **Dashboard** | Live download history, queue status, active download indicator, Sync Now button, source and status filters |
| **Requests** | Request any song by name or `Artist – Title` format |
| **Settings** | Playlist URL, poll interval, quality, sleep delay, file naming, sp_dc cookie, CSV import |

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
| `/data/spotify_auth.json` | Stored OAuth tokens (named volume `app_data`) |
| `/data/cookies.txt` | Optional YouTube cookies file |

## Buy me a coffee

If you appreciate my work!  
[Paypal.me](https://www.paypal.me/dcmbrbeats)

## License

This project is for personal use and educational purposes only. Do not use it to infringe on copyright laws.
