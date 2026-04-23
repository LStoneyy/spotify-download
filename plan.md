# Sonus - Audio Management System Roadmap

## Status Quo
Currently, the project is a sophisticated Spotify/YouTube downloader. It allows requesting single songs, importing CSVs, monitoring Spotify playlists, and uploading local files.

## Roadmap & Prioritization

### Phase 1: Foundation & Rebranding (Short term)
*Focus: Establishing the "Sonus" identity and expanding basic download capabilities.*
- **Rebranding**: Full UI/UX update to "Sonus" (Logo, Text, Themes).
- **Album Downloads**: Logic to fetch and download full albums via Spotify/YouTube.
- **Basic Library View**: A page to see all downloaded files (current state is mainly a history/queue).
- **Estimated Time**: 1-2 weeks.

### Phase 2: The "Library" Experience (Medium term)
*Focus: Transforming the downloader into a manager.*
- **Library Management**: 
    - Delete functionality (File + DB entry).
    - Folder-based organization on disk.
    - Internal Playlist creation and management.
- **Metadata Engine**:
    - Manual metadata editing (ID3 tags).
    - Loading and managing Cover Art.
- **Import Assistant**: Scan `MUSIC_DIR` to index existing local files into the DB.
- **Estimated Time**: 3-5 weeks.

### Phase 3: The "Audio Hub" (Medium-Long term)
*Focus: Consuming the music and improving quality.*
- **Web Player**: Fully functional audio player (Play/Pause, Seek, Volume, Queue) integrated into the UI.
- **Advanced Metadata**:
    - Auto-tagging integration (MusicBrainz/Discogs).
    - Audio analysis (Bitrate, Waveform).
- **Estimated Time**: 3-4 weeks.

### Phase 4: Ecosystem & Resilience (Long term)
*Focus: Stability, Backup and Scaling.*
- **Cloud Sync**: Backup options for S3/Nextcloud.
- **Streaming API**: Turning Sonus into a DLNA/UPnP or custom API server for external players.
- **Estimated Time**: 2-4 weeks.

### Phase 5: Professionalization (Future Scope)
*Focus: Multi-user and Power-user features.*
- **User Management**: User/Admin roles, private playlists.
- **Smart Playlists**: Rule-based dynamic playlists.
- **Mass-Editing**: Bulk metadata changes.
- **Estimated Time**: TBD.

## Summary Table
| Phase | Focus | Key Feature | Est. Duration |
| :--- | :--- | :--- | :--- |
| 1 | Identity | Rebranding & Albums | 1-2 Weeks |
| 2 | Management | Library & Import | 3-5 Weeks |
| 3 | Consumption | Web Player & Auto-Tags | 3-4 Weeks |
| 4 | Ecosystem | Cloud Sync & Streaming | 2-4 Weeks |
| 5 | Scaling | Multi-User & Smart Lists | TBD |
