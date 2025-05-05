import os
import re
import sys
import subprocess
import requests
import csv
import time
import random
from urllib.parse import quote
from rich.console import Console
from rich.progress import Progress
import yt_dlp
import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, TIT2, TPE1, TALB

console = Console()

def get_tracks_from_csv(file_path):
    tracks = []
    try:
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            field_names = reader.fieldnames
            
            if field_names:
                console.print(f"[green]Detected CSV fields: {', '.join(field_names)}[/green]")
                
                title_column = None
                artist_column = None
                album_column = None
                
                for column in field_names:
                    if column and 'track name' in column.lower():
                        title_column = column
                    if column and 'artist name' in column.lower():
                        artist_column = column
                    if column and 'album name' in column.lower():
                        album_column = column
                
                console.print(f"[cyan]Using the following columns:[/cyan]")
                console.print(f"[cyan]Title: {title_column}[/cyan]")
                console.print(f"[cyan]Artist: {artist_column}[/cyan]")
                console.print(f"[cyan]Album: {album_column}[/cyan]")
                
                csvfile.seek(0)
                reader = csv.DictReader(csvfile)
                
                for row in reader:
                    title = row.get(title_column, '').strip() if title_column else None
                    artist = row.get(artist_column, '').strip() if artist_column else None
                    album = row.get(album_column, '').strip() if album_column else None
                    
                    if title and title.startswith('"') and title.endswith('"'):
                        title = title[1:-1]
                    if artist and artist.startswith('"') and artist.endswith('"'):
                        artist = artist[1:-1]
                    if album and album.startswith('"') and album.endswith('"'):
                        album = album[1:-1]
                    
                    if title:
                        tracks.append({'title': title, 'artist': artist, 'album': album})
    
    except Exception as e:
        console.print(f"[red]Error reading CSV file: {e}[/red]")
    
    if tracks:
        console.print(f"[green]{len(tracks)} tracks loaded from CSV file.[/green]")
        for i, track in enumerate(tracks[:3]):
            artist_display = track['artist'] if track['artist'] else 'Unknown artist'
            console.print(f"[cyan]Example {i+1}: '{track['title']}' by '{artist_display}'[/cyan]")
    else:
        console.print("[red]No tracks found in CSV file![/red]")
    
    return tracks

def search_youtube(query):
    try:
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'default_search': 'ytsearch',
            'max_downloads': 1,
            'ignoreerrors': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'geo_bypass': True,
            'extractor_args': {'youtube': {'skip': ['hls', 'dash']}},
            'http_headers': {
                'User-Agent': 'Mozilla/5.0',
                'Accept-Language': 'de,en-US;q=0.9,en;q=0.8',
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_string = f"ytsearch1:{query}"
            console.print(f"[cyan]Full search query: {search_string}[/cyan]")
            search_results = ydl.extract_info(search_string, download=False)
            
            if not search_results or 'entries' not in search_results or not search_results['entries']:
                console.print(f"[yellow]No search results for: {query}[/yellow]")
                return None
                
            video = search_results['entries'][0]
            return f"https://www.youtube.com/watch?v={video['id']}"
    except Exception as e:
        console.print(f"[red]YouTube search error: {str(e)}[/red]")
        return None

def set_mp3_metadata(mp3_path, title, artist, album):
    try:
        try:
            audio = EasyID3(mp3_path)
        except mutagen.id3.ID3NoHeaderError:
            audio = mutagen.File(mp3_path, easy=True)
            audio.add_tags()
        
        audio['title'] = title
        if artist:
            audio['artist'] = artist
        if album:
            audio['album'] = album
        audio.save()
        
        try:
            tags = ID3(mp3_path)
            tags["TIT2"] = TIT2(encoding=3, text=title)
            if artist:
                tags["TPE1"] = TPE1(encoding=3, text=artist)
            if album:
                tags["TALB"] = TALB(encoding=3, text=album)
            tags.save(mp3_path)
        except Exception as e:
            console.print(f"[yellow]Warning using ID3 direct method: {e}[/yellow]")
            
        return True
    except Exception as e:
        console.print(f"[red]Error setting metadata for {mp3_path}: {e}[/red]")
        return False

def download_mp3(youtube_url, output_dir, track_info, quality='320'):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    title = track_info.get('title', '')
    artist = track_info.get('artist', '')
    album = track_info.get('album', '')
    
    file_title = f"{artist} - {title}" if artist else title
    file_title = file_title.strip().replace("/", "_").replace("\\", "_").replace(":", "-").replace("?", "").replace("*", "").replace("\"", "'").replace("<", "(").replace(">", ")").replace("|", "-")
    
    output_path = os.path.join(output_dir, f"{file_title}.mp3")
    if os.path.exists(output_path):
        console.print(f"[blue]Already exists: {file_title}[/blue]")
        return False

    temp_path = os.path.join(output_dir, f"temp_{file_title}.mp3")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': quality,
        }],
        'outtmpl': temp_path.replace(".mp3", ""),
        'quiet': True,
        'noplaylist': True,
        'no_warnings': True,
        'timeout': 30,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'extractor_args': {'youtube': {'skip': ['hls', 'dash']}},
        'http_headers': {
            'User-Agent': 'Mozilla/5.0',
            'Accept-Language': 'de,en-US;q=0.9,en;q=0.8',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
        
        downloaded_file = None
        for ext in ['.mp3', '.webm', '.m4a']:
            possible_file = temp_path.replace(".mp3", ext)
            if os.path.exists(possible_file):
                downloaded_file = possible_file
                break
        
        if not downloaded_file:
            console.print(f"[red]Download file not found for {file_title}[/red]")
            return False
        
        if downloaded_file != temp_path:
            os.rename(downloaded_file, temp_path)
        
        set_mp3_metadata(temp_path, title, artist, album)
        os.rename(temp_path, output_path)
        
        return True
    except Exception as e:
        console.print(f"[red]Error downloading {file_title}: {e}[/red]")
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        return False

def main():
    console.print("[bold blue]=== MP3 Downloader for Spotify CSV ===[/bold blue]")
    
    console.print("[yellow]Checking for yt-dlp updates...[/yellow]")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        console.print("[green]yt-dlp updated.[/green]")
    except Exception as e:
        console.print(f"[yellow]Could not update yt-dlp: {e}[/yellow]")
    
    # NEU: Eingaben über Umgebungsvariablen
    csv_file = os.environ.get("CSV_FILE", "livefreeandsleepgreat.csv").strip()
    output_dir = os.environ.get("OUTPUT_DIR", "Downloads").strip()
    quality = os.environ.get("QUALITY", "320").strip()

    if not os.path.isfile(csv_file):
        console.print(f"[red]CSV file not found: {csv_file}[/red]")
        return

    tracks = get_tracks_from_csv(csv_file)
    if not tracks:
        console.print("[red]No tracks found in the CSV![/red]")
        return

    with Progress() as progress:
        task = progress.add_task("[cyan]Downloading songs...", total=len(tracks))

        for track in tracks:
            title = track.get("title", "")
            artist = track.get("artist", "")
            
            if title is None:
                title = ""
            if artist is None:
                artist = ""
                
            title = title.strip()
            artist = artist.strip()
            
            if not title:
                progress.update(task, advance=1)
                continue

            file_title = f"{artist} - {title}" if artist else title
            file_title = file_title.strip().replace("/", "_").replace("\\", "_").replace(":", "-").replace("?", "").replace("*", "").replace("\"", "'").replace("<", "(").replace(">", ")").replace("|", "-")
            
            if os.path.exists(os.path.join(output_dir, f"{file_title}.mp3")):
                console.print(f"[blue]Skipped, already exists: {file_title}[/blue]")
                progress.update(task, advance=1)
                continue

            if not artist:
                console.print(f"[yellow]Warning: No artist found for \"{title}\"![/yellow]")
            
            if artist:
                search_query = f"{artist} - {title} official audio"
            else:
                search_query = f"{title} official audio"
            
            youtube_url = search_youtube(search_query)

            if youtube_url:
                success = download_mp3(youtube_url, output_dir, track, quality)
                if success:
                    console.print(f"[green]Downloaded: {file_title}[/green]")
                else:
                    console.print(f"[yellow]Skipped: {file_title}[/yellow]")
            else:
                console.print(f"[yellow]No result found for: {file_title}[/yellow]")
                if artist:
                    alt_search_query = f"{artist} {title}"
                else:
                    alt_search_query = title
                    
                youtube_url = search_youtube(alt_search_query)
                
                if youtube_url:
                    time.sleep(random.uniform(1.0, 3.0))
                    success = download_mp3(youtube_url, output_dir, track, quality)
                    if success:
                        console.print(f"[green]Downloaded with alternative search: {file_title}[/green]")
                    else:
                        console.print(f"[yellow]All search attempts failed: {file_title}[/yellow]")
                            
            time.sleep(random.uniform(1.0, 2.0))
            progress.update(task, advance=1)

    console.print(f"[green]Done! Songs saved in: {output_dir}[/green]")

if __name__ == "__main__":
    main()
