import os
import re
import subprocess
import requests
import csv
from urllib.parse import quote
from rich.console import Console
from rich.progress import Progress
import yt_dlp

console = Console()

def get_tracks_from_csv(file_path):
    tracks = []
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            title = row.get('Track Name', '').strip()
            artist = row.get('Artist Name', '').strip()
            if title:
                tracks.append({'title': title, 'artist': artist})
    return tracks

def search_youtube(query):
    try:
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'default_search': 'ytsearch',
            'max_downloads': 1,
            'ignoreerrors': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_results = ydl.extract_info(f"ytsearch1:{query}", download=False)
            if not search_results or 'entries' not in search_results or not search_results['entries']:
                return None
            video = search_results['entries'][0]
            return f"https://www.youtube.com/watch?v={video['id']}"
    except Exception as e:
        console.print(f"[red]YouTube search error: {e}[/red]")
        return None

def download_mp3(youtube_url, output_dir, file_title, quality='320'):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_path = os.path.join(output_dir, f"{file_title}.mp3")
    if os.path.exists(output_path):
        console.print(f"[blue]Already exists: {file_title}[/blue]")
        return False

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': quality,
        }],
        'outtmpl': output_path,
        'quiet': True,
        'noplaylist': True,
        'no_warnings': True,
        'timeout': 30
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
        return True
    except Exception as e:
        console.print(f"[red]Error downloading {file_title}: {e}[/red]")
        return False

def main():
    console.print("[bold blue]=== MP3 Downloader from Spotify CSV ===[/bold blue]")
    csv_file = input("Enter CSV filename (default: livefreeandsleepgreat.csv): ").strip()
    if not csv_file:
        csv_file = "livefreeandsleepgreat.csv"
    if not os.path.isfile(csv_file):
        console.print(f"[red]CSV file not found: {csv_file}[/red]")
        return

    tracks = get_tracks_from_csv(csv_file)
    if not tracks:
        console.print("[red]No tracks found in the CSV![/red]")
        return

    output_dir = input("Output folder (default: Downloads): ").strip()
    if not output_dir:
        output_dir = "Downloads"

    quality = input("MP3 quality (e.g. 320, best) [default: 320]: ").strip()
    if not quality:
        quality = "320"

    with Progress() as progress:
        task = progress.add_task("[cyan]Downloading songs...", total=len(tracks))

        for track in tracks:
            title = track.get("title", "").strip()
            artist = track.get("artist", "").strip()
            if not title:
                progress.update(task, advance=1)
                continue

            filename = f"{artist} - {title}".strip().replace("/", "_")
            if os.path.exists(os.path.join(output_dir, f"{filename}.mp3")):
                progress.update(task, advance=1)
                continue

            search_query = f"{artist} - {title} audio" if artist else f"{title} audio"
            youtube_url = search_youtube(search_query)

            if youtube_url:
                success = download_mp3(youtube_url, output_dir, filename, quality)
                if not success:
                    console.print(f"[yellow]Skipped: {filename}[/yellow]")
            else:
                console.print(f"[yellow]No result found: {filename}[/yellow]")

            progress.update(task, advance=1)

    console.print(f"[green]Done! Songs saved to: {output_dir}[/green]")

if __name__ == "__main__":
    main()
