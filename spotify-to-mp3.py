import os
import re
import subprocess
import requests
import json
from urllib.parse import quote
from rich.console import Console
from rich.progress import Progress

console = Console()

def get_tracks_from_csv(file_path):
    import csv
    tracks = []
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            title = row.get('Track Name', '').strip()
            artist = row.get('Artist Name', '').strip()
            if title:
                tracks.append({'title': title, 'artist': artist})
    return tracks


def extract_spotify_id(url):
    """Extrahiert die Spotify-ID aus einer URL"""
    if "spotify.com" not in url:
        return None, None
    
    # Playlist ID extrahieren
    playlist_match = re.search(r'playlist/([a-zA-Z0-9]+)', url)
    if playlist_match:
        return "playlist", playlist_match.group(1)
    
    # Album ID extrahieren
    album_match = re.search(r'album/([a-zA-Z0-9]+)', url)
    if album_match:
        return "album", album_match.group(1)
    
    # Track ID extrahieren
    track_match = re.search(r'track/([a-zA-Z0-9]+)', url)
    if track_match:
        return "track", track_match.group(1)
    
    return None, None

def get_tracks_from_soundloaders(url):
    """
    Verwendet api.soundloaders.com, um Tracks aus einer Spotify-URL zu extrahieren
    """
    spotify_type, spotify_id = extract_spotify_id(url)
    
    if not spotify_type or not spotify_id:
        console.print("[bold red]Konnte keine gültige Spotify-ID aus der URL extrahieren![/bold red]")
        return []
    
    console.print(f"[yellow]Extrahiere Tracks von Spotify mit SoundLoaders API...[/yellow]")
    
    api_url = f"https://api.soundloaders.com/spotify/{spotify_type}/{spotify_id}"
    
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        
        tracks = []
        
        if spotify_type == "playlist" or spotify_type == "album":
            if "tracks" in data:
                for track in data["tracks"]:
                    title = track.get("title", "Unknown Title")
                    artist = track.get("artist", "Unknown Artist")
                    tracks.append({"title": title, "artist": artist})
        elif spotify_type == "track":
            title = data.get("title", "Unknown Title")
            artist = data.get("artist", "Unknown Artist")
            tracks.append({"title": title, "artist": artist})
        
        console.print(f"[green]Erfolgreich {len(tracks)} Tracks gefunden![/green]")
        return tracks
    
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Fehler bei der API-Anfrage an SoundLoaders: {e}[/bold red]")
        console.print("[yellow]Versuche alternative Methode für das Extrahieren der Playlist...[/yellow]")
        return []

def is_youtube_playlist_url(url):
    """Prüft, ob es sich um eine YouTube-Playlist-URL handelt"""
    return "youtube.com/playlist" in url or "youtu.be" in url and "list=" in url

def fetch_youtube_playlist_tracks(playlist_url):
    """
    Extrahiert die Video-Titel aus einer YouTube-Playlist-URL mit yt-dlp
    """
    console.print(f"[yellow]Extrahiere Lieder aus der YouTube-Playlist...[/yellow]")
    
    try:
        # yt-dlp direkt für Playlist-Info verwenden
        import yt_dlp
        
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'force_generic_extractor': False,
            'ignoreerrors': True,
        }
        
        tracks = []
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            playlist_info = ydl.extract_info(playlist_url, download=False)
            
            if not playlist_info or 'entries' not in playlist_info:
                console.print("[bold red]Keine Videos in der Playlist gefunden![/bold red]")
                return []
            
            for entry in playlist_info['entries']:
                if entry:
                    title = entry.get('title', 'Unknown Title')
                    youtube_url = f"https://www.youtube.com/watch?v={entry['id']}"
                    
                    # Versuche, Künstler und Titel zu trennen (falls im Format "Künstler - Titel")
                    artist = ""
                    if " - " in title:
                        parts = title.split(" - ", 1)
                        artist = parts[0].strip()
                        title = parts[1].strip()
                    
                    tracks.append({
                        "title": title,
                        "artist": artist,
                        "youtube_url": youtube_url
                    })
        
        console.print(f"[green]Gefunden: {len(tracks)} Videos[/green]")
        return tracks
    
    except Exception as e:
        console.print(f"[bold red]Fehler beim Extrahieren der YouTube-Playlist: {e}[/bold red]")
        return []

def ask_for_manual_tracks():
    """
    Fragt den Benutzer nach manueller Eingabe der Tracks
    """
    tracks = []
    console.print("[yellow]Bitte gib die Lieder manuell ein (leere Zeile zum Beenden):[/yellow]")
    console.print("[cyan]Format: 'Künstler - Titel' oder 'Titel' oder komplette YouTube-URL[/cyan]")
    
    while True:
        track_input = input("Eingabe (leere Zeile zum Beenden): ")
        if not track_input:
            break
        
        # Prüfen, ob es sich um eine YouTube-URL handelt
        if track_input.startswith("http") and ("youtube.com" in track_input or "youtu.be" in track_input):
            tracks.append({
                "title": "YouTube Video",
                "artist": "",
                "youtube_url": track_input
            })
            console.print(f"[green]YouTube-URL hinzugefügt[/green]")
        else:
            # Versuchen, Künstler und Titel zu trennen
            parts = track_input.split('-', 1)
            if len(parts) == 2:
                artist = parts[0].strip()
                title = parts[1].strip()
                tracks.append({"title": title, "artist": artist})
            else:
                # Nur Titel ohne Künstler
                tracks.append({"title": track_input.strip(), "artist": ""})
            
            console.print(f"[green]Lied hinzugefügt[/green]")
    
    return tracks

def search_youtube(query):
    """
    Sucht auf YouTube nach dem angegebenen Query und gibt die erste Video-URL zurück
    Verwendet yt-dlp für die Suche
    """
    try:
        import yt_dlp
        
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'force_generic_extractor': False,
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
        console.print(f"[red]Fehler bei der YouTube-Suche: {e}[/red]")
        
        # Fallback zur URL-basierten Suche
        search_query = quote(query)
        youtube_search_url = f"https://www.youtube.com/results?search_query={search_query}"
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(youtube_search_url, headers=headers)
            response.raise_for_status()
            
            # Regulärer Ausdruck für Video-IDs
            video_ids = re.findall(r"watch\?v=(\S{11})", response.text)
            if video_ids:
                return f"https://www.youtube.com/watch?v={video_ids[0]}"
        except Exception as e2:
            console.print(f"[red]Fehler bei der YouTube-Suche (Fallback): {e2}[/red]")
        
        return None

def download_mp3(youtube_url, output_dir, quality='best'):
    """
    Lädt das Video als MP3 herunter und speichert es im angegebenen Verzeichnis
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Optionen für yt-dlp
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': quality,
        }],
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True
    }
    
    try:
        with subprocess.Popen(['yt-dlp', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
            proc.communicate()
            if proc.returncode != 0:
                console.print("[bold red]yt-dlp ist nicht installiert! Bitte installiere es mit 'pip install yt-dlp'[/bold red]")
                return False
        
        with subprocess.Popen(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
            proc.communicate()
            if proc.returncode != 0:
                console.print("[bold red]ffmpeg ist nicht installiert! Bitte installiere es auf deinem System.[/bold red]")
                return False
        
        import yt_dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
        return True
    except Exception as e:
        console.print(f"[bold red]Fehler beim Download: {e}[/bold red]")
        return False

def main():
    console.print("[bold blue]===== Musik zu MP3 Downloader =====[/bold blue]")
    
    # Eingabequelle abfragen
    console.print("[yellow]Wähle eine Eingabequelle:[/yellow]")
    console.print("1. Spotify-Playlist/Album/Track URL")
    console.print("2. YouTube-Playlist URL")
    console.print("3. Manuelle Eingabe der Lieder")
    console.print("4. CSV-Datei (Exportify-Export)")

    
    choice = input("Wähle eine Option (1-3): ")
    
    tracks = []
    
    if choice == "1":
        playlist_url = input("Gib die Spotify-URL ein: ")
        if "spotify.com" in playlist_url:
            tracks = get_tracks_from_soundloaders(playlist_url)
            
            if not tracks:
                console.print("[yellow]Konnte keine Tracks mit SoundLoaders extrahieren. Bitte versuche die manuelle Eingabe.[/yellow]")
                tracks = ask_for_manual_tracks()
        else:
            console.print("[bold red]Die URL scheint keine gültige Spotify-URL zu sein![/bold red]")
            tracks = ask_for_manual_tracks()
    elif choice == "2":
        playlist_url = input("Gib die URL der YouTube-Playlist ein: ")
        if is_youtube_playlist_url(playlist_url):
            tracks = fetch_youtube_playlist_tracks(playlist_url)
            
            if not tracks:
                console.print("[yellow]Konnte keine Videos aus der Playlist extrahieren. Bitte versuche die manuelle Eingabe.[/yellow]")
                tracks = ask_for_manual_tracks()
        else:
            console.print("[bold red]Die URL scheint keine gültige YouTube-Playlist-URL zu sein![/bold red]")
            tracks = ask_for_manual_tracks()
    elif choice == "4":
        csv_file = input("Pfad zur CSV-Datei (Standard: 'livefreeandsleepgreat.csv'): ").strip()
        if not csv_file:
            csv_file = "livefreeandsleepgreat.csv"
        if os.path.isfile(csv_file):
            tracks = get_tracks_from_csv(csv_file)
            console.print(f"[green]{len(tracks)} Tracks aus CSV geladen![/green]")
    else:
        console.print(f"[bold red]Datei '{csv_file}' nicht gefunden![/bold red]")

    
    if not tracks:
        console.print("[bold red]Keine Lieder zum Herunterladen gefunden![/bold red]")
        return
    
    # Zielordner abfragen
    default_output_dir = "Downloads"
    output_dir = input(f"Zielordner für die MP3s (Standard: {default_output_dir}): ")
    if not output_dir:
        output_dir = default_output_dir
    
    # MP3-Qualität abfragen
    default_quality = "320"
    quality = input(f"MP3-Qualität (0-9 oder 'best' für beste Qualität, Standard: {default_quality}): ")
    if not quality:
        quality = default_quality
    
    # Jeden Track auf YouTube suchen und herunterladen
    with Progress() as progress:
        task = progress.add_task("[cyan]Lieder werden heruntergeladen...", total=len(tracks))
        
        for i, track in enumerate(tracks):
            # Prüfen, ob bereits eine YouTube-URL vorhanden ist
            if "youtube_url" in track and track["youtube_url"]:
                youtube_url = track["youtube_url"]
                display_name = track["title"]
                progress.update(task, description=f"[green]Downloade: {display_name}")
            else:
                # Auf YouTube suchen
                query = f"{track['artist']} {track['title']} audio" if track['artist'] else f"{track['title']} audio"
                display_name = f"{track['artist']} - {track['title']}" if track['artist'] else track['title']
                
                progress.update(task, description=f"[cyan]Suche nach: {display_name}")
                youtube_url = search_youtube(query)
            
            # Download
            if youtube_url:
                progress.update(task, description=f"[green]Downloade: {display_name}")
                success = download_mp3(youtube_url, output_dir, quality)
                if success:
                    progress.update(task, advance=1)
                else:
                    progress.update(task, description=f"[red]Fehler beim Download von {display_name}")
                    progress.update(task, advance=1)
            else:
                console.print(f"[yellow]Konnte kein YouTube-Video für '{display_name}' finden[/yellow]")
                progress.update(task, advance=1)
    
    console.print("[bold green]Download abgeschlossen![/bold green]")
    console.print(f"Die MP3s wurden im Ordner '{output_dir}' gespeichert.")

if __name__ == "__main__":
    main()