# Spotify Playlist Downloader (CSV)
![Spotify Downloader Icon](./icon.ico)

This Python script downloads MP3 files of tracks listed in a CSV file, typically exported from a Spotify playlist using [Exportify.net](https://exportify.net/).

## Features

- Reads a CSV file with track titles and artist names
- Searches for each track on YouTube
- Downloads the best audio version and converts it to MP3
- Skips tracks that already exist in the target folder
- Handles errors and skips problematic downloads (including timeouts)
- Uses a 60-second timeout for downloads to avoid long hangs
- **NEW: Graphical User Interface (GUI) for easier use**

## Requirements

- Python 3.6+
- yt-dlp (`pip install yt-dlp`)
- ffmpeg (must be installed and accessible via command line)
- rich (`pip install rich`)
- customtkinter (`pip install customtkinter`)
- packaging (`pip install packaging`)

**Windows users can now use the included .exe and don't need to meet these requirements!**

## Installation

Instead of downloading everything yourself, just login on [Exportify.net](https://exportify.net/) and download the csv of the playlists you want to download. 

Then clone this repo using 
```bash
git clone https://github.com/LStoneyy/spotify-download.git
```

Install all the required packages:
```bash
pip install -r requirements.txt
```

## Usage

### Command Line Interface
1. Place your Spotify-exported CSV file (e.g., `livefreeandsleepgreat.csv`) in the same folder.
2. Run the script:
   ```bash
   python spotify-downloaderCLI.py
   ```
3. Follow the prompts:
   - Provide the CSV filename, then press Enter
   - Provide the output directory (or press Enter for "Downloads")
   - Choose MP3 quality (e.g., 320)

### Graphical User Interface (GUI)
1. Run the GUI application using Python:
   ```bash
   python spotify-downloaderGUI.py
   ```
2. Use the interface to:
   - Open Exportify in your browser to get your playlist CSV
   - Select your CSV file using the file browser
   - Choose your output directory
   - Set the desired MP3 quality
   - Start the download process with a single click

### Executable Version
You can also download the pre-built executable from the releases section, which includes all dependencies and doesn't require a Python installation. Just click on the spotify-downloadGUI.exe and follow the steps above.

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
- The GUI version provides a more user-friendly experience with no command-line knowledge required.

## Buy me a coffee

If you appreciate my work! I do not sell or try to sell anything, this is just to show your appreciation (I do appreciate it immensely!)
[Paypal.me](https://www.paypal.me/dcmbrbeats)

## License

This project is for personal use and educational purposes only. Do not use it to infringe on copyright laws.

