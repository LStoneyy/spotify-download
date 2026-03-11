# Sonus

<p align="center">
  <img src="frontend/public/logo.svg" alt="Sonus Logo" width="128" height="128">
</p>

**Sonus** is a self-hosted universal music hub that downloads music as MP3s into your
music directory. A React web UI at **http://localhost:6767** lets you request
songs manually, import Spotify playlists via CSV, monitor playlists automatically,
and configure all settings.

> **Note:** This project was formerly known as "Spotify Playlist Downloader" and has been rebranded to **Sonus** as part of a larger evolution into a universal music management platform.

## Features

- **YouTube search** with token-based scoring and smart fallbacks
- **Rate-limit-safe downloads**: configurable sleep between tracks, exponential backoff on 429s
- Uses the YouTube `tv` client (no PO Token required)
- Optional `cookies.txt` support for improved resilience
- ID3 tag writing (title, artist, album)
- **Responsive web UI** — works great on mobile and desktop
- **PWA support** — install as an app on your device
- **Multilingual support** — English and German translations built-in; easily extensible to more languages
- **Manual song request** via the web UI
- **CSV playlist import** (Exportify format or plain `Artist - Title` lists)
- **Automatic playlist monitoring** — syncs playlists hourly, downloads new tracks
- **Spotify OAuth integration** — login to access your playlists
- **Upload local music files** — drop any audio file (MP3, WAV, FLAC, M4A, OGG, WMA, AAC, OPUS) directly into your library; non-MP3 formats are automatically converted
- Configurable file naming templates with live preview
- De-duplication by Spotify ID and by title + artist
- All state persisted in SQLite (survives restarts)

## Requirements

- Docker + Docker Compose
- A Spotify Developer App (free) for playlist monitoring

## Setup

### 1. Clone

```bash
git clone https://github.com/LStoneyy/sonus.git
cd spotify-download
```

### 2. Create a Spotify App

1. Go to https://developer.spotify.com/dashboard
2. Click **"Create App"**
3. Fill in the name and description
4. When asked "Which API/SDKs are you planning to use?", select **Web API**
5. After creating, click on your app and go to **Settings**
6. Copy the **Client ID** and **Client Secret**
7. Under **Redirect URIs**, add:
   ```
   http://127.0.0.1:6767/api/auth/callback
   ```
8. Click **Save**

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
# Spotify API credentials (from step 2)
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
SPOTIFY_REDIRECT_URI=http://127.0.0.1:6767/api/auth/callback

# Music output directory (absolute path on your host machine)
MUSIC_DIR=/absolute/path/to/your/music/folder

# Optional: YouTube cookies for better reliability
# COOKIES_PATH=/absolute/path/to/cookies.txt
```

### 4. Start

```bash
docker compose up --build -d
```

Open **http://localhost:6767** in your browser.

## Usage

### Manual Song Request

Go to **Requests**, type any song name or `Artist – Title` and hit Enter. It's queued immediately.

### Upload a Local File

Already have the file on your computer? Go to **Requests → Upload from computer** and click **"Upload Music File"**. A modal opens where you:

1. Pick an audio file from your computer (MP3, WAV, FLAC, M4A, OGG, WMA, AAC, OPUS, or WEBM)
2. Enter the **Title** and **Artist** (required) and optionally the **Album**
3. Click **Upload**

The file is saved straight to your music directory. Non-MP3 formats are automatically converted to MP3 using FFmpeg at your configured quality setting. ID3 tags are written and the filename follows your file naming template — exactly the same as a regular download.

> **Note:** If a file with the same name already exists in the music directory the upload is rejected with a conflict error.

### CSV Import

Export your Spotify playlist with [Exportify](https://exportify.net), then go to **Settings → Import Playlist CSV** and upload the file. All tracks are queued and deduplicated automatically.

### Playlist Monitoring

1. Go to **Settings → Spotify Authentication**
2. Click **"Login with Spotify"**
3. Authorize the app in Spotify
4. You'll be redirected back to Settings
5. Under **"Monitored Playlists"**, paste a Spotify playlist URL and click **"Add"**
6. All tracks will be queued for download
7. Playlists are synced hourly — new tracks are downloaded automatically

You can also click **"Sync"** on any monitored playlist to force an immediate sync.

## CSV Import Formats

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
| **Requests** | Request any song by name or `Artist – Title` format; upload local audio files |
| **Settings** | Quality, sleep delay, file naming, CSV import, Spotify auth, playlist monitoring |

## File Naming Templates

| Template | Example output |
|----------|---------------|
| `{artist} - {title}` *(default)* | `The Weeknd - Blinding Lights.mp3` |
| `{title}` | `Blinding Lights.mp3` |
| `{album}/{artist} - {title}` | `After Hours/The Weeknd - Blinding Lights.mp3` |

## Optional: YouTube Cookies

Mount a `cookies.txt` (Netscape format) to improve download reliability on rate-limited IPs.

How to export:
1. Install the **Get cookies.txt LOCALLY** extension in Chrome/Firefox
2. Go to [youtube.com](https://www.youtube.com) while logged in
3. Click the extension icon and export `cookies.txt`
4. Set `COOKIES_PATH` in your `.env`:

```env
COOKIES_PATH=/absolute/path/to/cookies.txt
```

## Volume Layout

| Container path | Description |
|----------------|-------------|
| `/music` | Your host music folder (`MUSIC_DIR`) |
| `/data/db.sqlite` | SQLite database (named volume `app_data`) |
| `/data/cookies.txt` | Optional YouTube cookies file |

## PWA Installation

The app works as a Progressive Web App (PWA). To install:

**Desktop (Chrome/Edge):**
1. Open http://localhost:6767
2. Click the install icon in the address bar
3. Click "Install"

**Mobile (iOS):**
1. Open http://localhost:6767 in Safari
2. Tap the share button
3. Tap "Add to Home Screen"

**Mobile (Android):**
1. Open http://localhost:6767 in Chrome
2. Tap the menu (three dots)
3. Tap "Add to Home Screen"

## Tech Stack

- **Backend**: Python, FastAPI, SQLModel, Spotipy, yt-dlp, FFmpeg
- **Frontend**: React, TypeScript, TailwindCSS, React Router, i18next
- **Database**: SQLite
- **Container**: Docker, Docker Compose

## Buy me a coffee

If you appreciate my work!  
[Paypal.me](https://www.paypal.me/dcmbrbeats)

## License

This project is for personal use and educational purposes only. Do not use it to infringe on copyright laws.
