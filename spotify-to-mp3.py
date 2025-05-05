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
            # Versuche zuerst mit dem Standard-CSV-Reader
            reader = csv.DictReader(csvfile)
            field_names = reader.fieldnames
            
            if field_names:
                # Zeige gefundene Felder an
                console.print(f"[green]Gefundene CSV-Felder: {', '.join(field_names)}[/green]")
                
                # Finde die korrekten Spalten für Titel, Künstler und Album
                title_column = None
                artist_column = None
                album_column = None
                
                # Suche nach den richtigen Spaltennamen
                for column in field_names:
                    if column and 'track name' in column.lower():
                        title_column = column
                    if column and 'artist name' in column.lower():
                        artist_column = column
                    if column and 'album name' in column.lower():
                        album_column = column
                
                console.print(f"[cyan]Verwende folgende Spalten:[/cyan]")
                console.print(f"[cyan]Title: {title_column}[/cyan]")
                console.print(f"[cyan]Artist: {artist_column}[/cyan]")
                console.print(f"[cyan]Album: {album_column}[/cyan]")
                
                # Setze die CSV zurück und lese erneut
                csvfile.seek(0)
                reader = csv.DictReader(csvfile)
                
                for row in reader:
                    title = row.get(title_column, '').strip() if title_column else None
                    artist = row.get(artist_column, '').strip() if artist_column else None
                    album = row.get(album_column, '').strip() if album_column else None
                    
                    # Überprüfe auf Anführungszeichen in den Feldern und entferne sie
                    if title and title.startswith('"') and title.endswith('"'):
                        title = title[1:-1]
                    if artist and artist.startswith('"') and artist.endswith('"'):
                        artist = artist[1:-1]
                    if album and album.startswith('"') and album.endswith('"'):
                        album = album[1:-1]
                    
                    if title:
                        tracks.append({'title': title, 'artist': artist, 'album': album})
    
    except Exception as e:
        console.print(f"[red]Fehler beim Lesen der CSV-Datei: {e}[/red]")
    
    if tracks:
        console.print(f"[green]{len(tracks)} Tracks aus der CSV-Datei geladen.[/green]")
        # Zeige die ersten 3 Tracks als Beispiel
        for i, track in enumerate(tracks[:3]):
            artist_display = track['artist'] if track['artist'] else 'Unbekannter Künstler'
            console.print(f"[cyan]Beispiel {i+1}: '{track['title']}' von '{artist_display}'[/cyan]")
    else:
        console.print("[red]Keine Tracks in der CSV-Datei gefunden![/red]")
    
    return tracks

def search_youtube(query):
    try:
        # Umgehung der YouTube-Einschränkungen
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'default_search': 'ytsearch',
            'max_downloads': 1,
            'ignoreerrors': True,
            'no_warnings': True,
            # Anti-Bot-Erkennung umgehen
            'nocheckcertificate': True,
            'geo_bypass': True,
            'extractor_args': {'youtube': {'skip': ['hls', 'dash']}},
            # User-Agent setzen
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'de,en-US;q=0.9,en;q=0.8',
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Eindeutige und vollständige Suchanfrage
            search_string = f"ytsearch1:{query}"
            console.print(f"[cyan]Vollständige Suchanfrage: {search_string}[/cyan]")
            search_results = ydl.extract_info(search_string, download=False)
            
            if not search_results or 'entries' not in search_results or not search_results['entries']:
                console.print(f"[yellow]Keine Suchergebnisse für: {query}[/yellow]")
                return None
                
            video = search_results['entries'][0]
            return f"https://www.youtube.com/watch?v={video['id']}"
    except Exception as e:
        console.print(f"[red]YouTube-Suchfehler: {str(e)}[/red]")
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
        if artist:
            audio['artist'] = artist
        if album:
            audio['album'] = album
        audio.save()
        
        # Falls EasyID3 nicht funktioniert hat, versuche es mit ID3 direkt
        try:
            tags = ID3(mp3_path)
            tags["TIT2"] = TIT2(encoding=3, text=title)
            if artist:
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
    file_title = file_title.strip().replace("/", "_").replace("\\", "_").replace(":", "-").replace("?", "").replace("*", "").replace("\"", "'").replace("<", "(").replace(">", ")").replace("|", "-")
    
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
        'timeout': 30,
        # YouTube-Einschränkungen umgehen
        'nocheckcertificate': True,
        'geo_bypass': True,
        'extractor_args': {'youtube': {'skip': ['hls', 'dash']}},
        # User-Agent setzen
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'de,en-US;q=0.9,en;q=0.8',
        }
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
    
    # Überprüfen und Updaten von yt-dlp
    console.print("[yellow]Prüfe auf yt-dlp Updates...[/yellow]")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        console.print("[green]yt-dlp wurde aktualisiert.[/green]")
    except Exception as e:
        console.print(f"[yellow]Konnte yt-dlp nicht aktualisieren: {e}[/yellow]")
    
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
            title = track.get("title", "")
            artist = track.get("artist", "")
            
            # Überprüfung gegen None-Werte
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
                console.print(f"[blue]Übersprungen, existiert bereits: {file_title}[/blue]")
                progress.update(task, advance=1)
                continue

            # Überprüfen, ob der Künstlername vorhanden ist
            if not artist:
                console.print(f"[yellow]Warnung: Kein Künstler für \"{title}\" gefunden![/yellow]")
            
            # Immer mit Künstler suchen, wenn dieser verfügbar ist
            if artist:
                search_query = f"{artist} - {title} official audio"
                console.print(f"[cyan]Suche mit Künstler: {search_query}[/cyan]")
            else:
                search_query = f"{title} official audio"
                console.print(f"[cyan]Suche ohne Künstler: {search_query}[/cyan]")
            
            youtube_url = search_youtube(search_query)

            if youtube_url:
                success = download_mp3(youtube_url, output_dir, track, quality)
                if success:
                    console.print(f"[green]Heruntergeladen: {file_title}[/green]")
                else:
                    console.print(f"[yellow]Übersprungen: {file_title}[/yellow]")
            else:
                console.print(f"[yellow]Kein Ergebnis gefunden für: {file_title}[/yellow]")
                # Alternative Suche ohne "official audio" versuchen
                if artist:
                    alt_search_query = f"{artist} {title}"
                else:
                    alt_search_query = title
                    
                console.print(f"[cyan]Alternative Suche: {alt_search_query}[/cyan]")
                youtube_url = search_youtube(alt_search_query)
                
                if youtube_url:
                    # Kurze Pause vor dem nächsten Download, um YouTube-Limits zu vermeiden
                    time.sleep(random.uniform(1.0, 3.0))
                    success = download_mp3(youtube_url, output_dir, track, quality)
                    if success:
                        console.print(f"[green]Heruntergeladen mit alternativer Suche: {file_title}[/green]")
                    else:
                        # Dritter Versuch mit kürzerem Suchbegriff
                        if artist:
                            final_search_query = f"{artist} {title.split()[0] if title.split() else title}"
                            console.print(f"[cyan]Letzte Suche mit Künstler und Titelbeginn: {final_search_query}[/cyan]")
                            youtube_url = search_youtube(final_search_query)
                            
                            if youtube_url:
                                time.sleep(random.uniform(1.0, 3.0))
                                success = download_mp3(youtube_url, output_dir, track, quality)
                                if success:
                                    console.print(f"[green]Heruntergeladen mit letzter Suche: {file_title}[/green]")
                                else:
                                    console.print(f"[yellow]Alle Suchversuche fehlgeschlagen: {file_title}[/yellow]")
                        else:
                            console.print(f"[yellow]Alternative Suche fehlgeschlagen: {file_title}[/yellow]")
                            
            # Kurze Pause zwischen den Downloads, um YouTube-Limits zu vermeiden
            time.sleep(random.uniform(1.0, 2.0))
            progress.update(task, advance=1)

    console.print(f"[green]Fertig! Lieder gespeichert in: {output_dir}[/green]")

if __name__ == "__main__":
    main()