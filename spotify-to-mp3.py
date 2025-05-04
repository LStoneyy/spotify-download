import os
import re
import subprocess
import requests
import csv
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
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            title = row.get('Track Name', '').strip()
            artist = row.get('Artist Name', '').strip()
            album = row.get('Album Name', '').strip()
            if title:
                tracks.append({'title': title, 'artist': artist, 'album': album})
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

def set_mp3_metadata(mp3_path, title, artist, album):
    try:
        # Versuche zuerst mit EasyID3
        try:
            audio = EasyID3(mp3_path)
        except mutagen.id3.ID3NoHeaderError:
            # Falls keine ID3-Header existieren, erstelle sie
            audio = mutagen.File(mp3_path, easy=True)
            audio.add_tags()
        
        # Setze die Metadaten
        audio['title'] = title
        audio['artist'] = artist
        if album:
            audio['album'] = album
        audio.save()
        
        # Falls EasyID3 nicht funktioniert hat, versuche es mit ID3 direkt
        try:
            tags = ID3(mp3_path)
            tags["TIT2"] = TIT2(encoding=3, text=title)
            tags["TPE1"] = TPE1(encoding=3, text=artist)
            if album:
                tags["TALB"] = TALB(encoding=3, text=album)
            tags.save(mp3_path)
        except Exception as e:
            console.print(f"[yellow]Warnung bei ID3-Direkt-Methode: {e}[/yellow]")
            
        return True
    except Exception as e:
        console.print(f"[red]Fehler beim Setzen der Metadaten für {mp3_path}: {e}[/red]")
        return False

def download_mp3(youtube_url, output_dir, track_info, quality='320'):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    title = track_info.get('title', '')
    artist = track_info.get('artist', '')
    album = track_info.get('album', '')
    
    file_title = f"{artist} - {title}" if artist else title
    file_title = file_title.strip().replace("/", "_").replace("\\", "_")
    
    output_path = os.path.join(output_dir, f"{file_title}.mp3")
    if os.path.exists(output_path):
        console.print(f"[blue]Existiert bereits: {file_title}[/blue]")
        return False

    # Temporärer Dateiname für den Download
    temp_path = os.path.join(output_dir, f"temp_{file_title}.mp3")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': quality,
        }],
        'outtmpl': temp_path.replace(".mp3", ""),  # yt-dlp fügt die Erweiterung selbst hinzu
        'quiet': True,
        'noplaylist': True,
        'no_warnings': True,
        'timeout': 30
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
        
        # Prüfen, ob die Datei existiert (yt-dlp könnte .webm oder andere Erweiterung nutzen)
        downloaded_file = None
        for ext in ['.mp3', '.webm', '.m4a']:
            possible_file = temp_path.replace(".mp3", ext)
            if os.path.exists(possible_file):
                downloaded_file = possible_file
                break
        
        if not downloaded_file:
            console.print(f"[red]Download-Datei nicht gefunden für {file_title}[/red]")
            return False
        
        # Umbenenne die Datei bei Bedarf
        if downloaded_file != temp_path:
            os.rename(downloaded_file, temp_path)
        
        # Setze Metadaten
        set_mp3_metadata(temp_path, title, artist, album)
        
        # Finale Umbenennung
        os.rename(temp_path, output_path)
        
        return True
    except Exception as e:
        console.print(f"[red]Fehler beim Download von {file_title}: {e}[/red]")
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        return False

def main():
    console.print("[bold blue]=== MP3 Downloader für Spotify CSV ===[/bold blue]")
    csv_file = input("CSV-Dateiname eingeben (Standard: livefreeandsleepgreat.csv): ").strip()
    if not csv_file:
        csv_file = "livefreeandsleepgreat.csv"
    if not os.path.isfile(csv_file):
        console.print(f"[red]CSV-Datei nicht gefunden: {csv_file}[/red]")
        return

    tracks = get_tracks_from_csv(csv_file)
    if not tracks:
        console.print("[red]Keine Tracks in der CSV gefunden![/red]")
        return

    output_dir = input("Ausgabeordner (Standard: Downloads): ").strip()
    if not output_dir:
        output_dir = "Downloads"

    quality = input("MP3-Qualität (z.B. 320, best) [Standard: 320]: ").strip()
    if not quality:
        quality = "320"

    with Progress() as progress:
        task = progress.add_task("[cyan]Lieder werden heruntergeladen...", total=len(tracks))

        for track in tracks:
            title = track.get("title", "").strip()
            artist = track.get("artist", "").strip()
            
            if not title:
                progress.update(task, advance=1)
                continue

            file_title = f"{artist} - {title}" if artist else title
            file_title = file_title.strip().replace("/", "_").replace("\\", "_")
            
            if os.path.exists(os.path.join(output_dir, f"{file_title}.mp3")):
                console.print(f"[blue]Übersprungen, existiert bereits: {file_title}[/blue]")
                progress.update(task, advance=1)
                continue

            # Verbesserte Suchlogik - Immer Künstler und Titel verwenden, wenn verfügbar
            search_query = f"{artist} {title} audio" if artist else f"{title} audio"
            console.print(f"[cyan]Suche: {search_query}[/cyan]")
            youtube_url = search_youtube(search_query)

            if youtube_url:
                success = download_mp3(youtube_url, output_dir, track, quality)
                if success:
                    console.print(f"[green]Heruntergeladen: {file_title}[/green]")
                else:
                    console.print(f"[yellow]Übersprungen: {file_title}[/yellow]")
            else:
                console.print(f"[yellow]Kein Ergebnis gefunden für: {file_title}[/yellow]")

            progress.update(task, advance=1)

    console.print(f"[green]Fertig! Lieder gespeichert in: {output_dir}[/green]")

if __name__ == "__main__":
    main()