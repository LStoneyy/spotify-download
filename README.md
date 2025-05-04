# Spotify Playlist Downloader (CSV)

This Python script downloads MP3 files of tracks listed in a CSV file, typically exported from a Spotify playlist using [Exportify.net](https://exportify.net/).

## Features

- Reads a CSV file with track titles and artist names
- Searches for each track on YouTube
- Downloads the best audio version and converts it to MP3
- Skips tracks that already exist in the target folder
- Handles errors and skips problematic downloads (including timeouts)
- Uses a 60-second timeout for downloads to avoid long hangs

## Requirements

- Python 3.6+
- yt-dlp (`pip install yt-dlp`)
- ffmpeg (must be installed and accessible via command line)
- rich (`pip install rich`)

## Installation

Instead of downloading everything yourself, just login on[Exportify.net](https://exportify.net/) and download the csv of the playlists you want to download. 

Then clone this repo using 
```bash
git clone https://github.com/LStoneyy/spotify-download.git
```

## Usage

1. Place your Spotify-exported CSV file (e.g., `livefreeandsleepgreat.csv`) in the same folder.
2. Run the script:
   ```bash
   python spotify-to-mp3.py
   ```
3. Follow the prompts:
   - Provide the CSV filename, then press Enter
   - Provide the output directory (or press Enter for "Downloads")
   - Choose MP3 quality (e.g., 320)

## CSV Format

Your CSV file should include the columns:

- `Track Name`
- `Artist Name`

Example:

```csv
Track Name,Artist Name
Blinding Lights,The Weeknd
bad guy,Billie Eilish
```

## Notes

- Existing MP3s will not be re-downloaded.
- If a video takes too long to download, it will be skipped after 60 seconds.
- Download results and errors will be printed in the console.

## License

This project is for personal use and educational purposes only. Do not use it to infringe on copyright laws.
