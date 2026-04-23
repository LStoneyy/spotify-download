# Sonus - Agent Context & Project Knowledge

## Project Overview
Sonus is evolving from a sophisticated Spotify/YouTube downloader into a complete, self-hosted Audio Management System. The goal is to provide a universal hub for managing a personal music collection with high-quality metadata, organized storage, and integrated playback.

## Core Tech Stack
- **Backend**: Python, FastAPI, SQLModel, Spotipy, yt-dlp, FFmpeg
- **Frontend**: React, TypeScript, TailwindCSS, React Router, i18next
- **Database**: SQLite (Persists download history, settings, and library state)
- **Infrastructure**: Docker & Docker Compose

## Strategic Roadmap
The project is developed in phases to ensure stability and provide clear milestones for content creation:

### Phase 1: Foundation & Rebranding
- **Focus**: Identity and expanded download capabilities.
- **Key Goals**: Full "Sonus" rebranding, Album download logic, Basic Library View.

### Phase 2: The "Library" Experience
- **Focus**: Management and organization.
- **Key Goals**: File deletion, Folder-based organization, Internal Playlists, Metadata editing, Local file import assistant.

### Phase 3: The "Audio Hub"
- **Focus**: Consumption and quality.
- **Key Goals**: Integrated Web Player, Auto-tagging (MusicBrainz/Discogs), Audio analysis (Waveforms).

### Phase 4: Ecosystem & Resilience
- **Focus**: Stability and external access.
- **Key Goals**: Cloud Backup (S3/Nextcloud), Streaming API for external players.

### Phase 5: Professionalization
- **Focus**: Scaling and power-user features.
- **Key Goals**: Multi-user support (User/Admin), Smart Playlists, Bulk editing.

## Key Guidelines for Future Agents
- **Maintain PWA Standards**: Ensure all new frontend features remain responsive and PWA-compatible.
- **Resilience First**: Always consider rate-limiting (YouTube) and file system edge cases (permissions, duplicates).
- **Consistent Branding**: All new UI components must align with the "Sonus" aesthetic.
- **Database Integrity**: Ensure that file system changes (deletions/moves) are always mirrored in the SQLite database to prevent orphaned entries.

## Important Paths
- Backend logic: `/backend/app`
- Frontend components: `/frontend/src/components`
- Roadmap: `plan.md`
