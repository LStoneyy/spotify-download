# Spotify Playlist Downloader

A self-hosted Docker Compose service that monitors a public Spotify playlist and
automatically downloads new tracks as MP3s into your music directory.  
A React web UI at **http://localhost:6767** lets you monitor downloads, request
songs manually, and configure all settings.

## Features

- Automatic playlist polling — detects new tracks and queues them
- YouTube search with smart fallbacks (primary → artist+title → first-word fallback)
- Rate-limit–safe downloads: configurable sleep between tracks, exponential backoff on 429s
- Uses the YouTube `tv` client (no PO Token required)
- Optional `cookies.txt` support for improved resilience
- ID3 tag writing (title, artist, album)
- Responsive web UI — works great on mobile and desktop
- Manual song request via the web UI
- Configurable file naming templates with live preview
- All state persisted in SQLite (survives restarts)

## Requirements

- Docker + Docker Compose
- A free [Spotify Developer App](https://developer.spotify.com/dashboard) (for API credentials)
- A public Spotify playlist

## Setup

### 1. Clone

```bash
git clone https://github.com/LStoneyy/spotify-download.git
cd spotify-download
```

### 2. Create a Spotify Developer App

1. Go to [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
2. Click **Create app**
3. Fill in any name/description
4. For **Redirect URI** enter `http://127.0.0.1:6767`
   - `localhost` is **not** allowed by Spotify
   - Must be an explicit loopback IP **with a port number**: `http://127.0.0.1:PORT`
   - The URI is never actually visited — Client Credentials flow never
     redirects a browser (6767 matches this project's web UI port)
5. Copy your **Client ID** and **Client Secret**

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

### 5. Configure in the UI

1. Go to **Settings** → paste your Spotify playlist URL → **Save settings**
2. Click **Sync Now** on the Dashboard to trigger the first poll
3. New tracks will be downloaded automatically on every poll interval

## Web UI

| Page | Description |
|------|-------------|
| **Dashboard** | Live download history, queue status, currently downloading indicator, Sync Now button |
| **Requests** | Request any song by name or `Artist – Title` format |
| **Settings** | Playlist URL, poll interval, quality, sleep delay, file naming template |

## File naming templates

| Template | Example output |
|----------|---------------|
| `{artist} - {title}` *(default)* | `The Weeknd - Blinding Lights.mp3` |
| `{title}` | `Blinding Lights.mp3` |
| `{album}/{artist} - {title}` | `After Hours/The Weeknd - Blinding Lights.mp3` |

## Optional: YouTube cookies

Mount a `cookies.txt` (Netscape format) to improve download reliability on
rate-limited IPs. Add to `docker-compose.yml` under `backend → volumes`:

```yaml
- /path/to/cookies.txt:/data/cookies.txt:ro
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

