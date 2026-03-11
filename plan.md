# Sonus - Self-Hosted Universal Music Hub

## Complete AI Development Instructions

### Project Overview

Transform the existing spotify-download application [1] into **Sonus** — a comprehensive, self-hosted music management platform. Sonus shall serve as the single application for acquiring, curating, and experiencing music from any source, regardless of origin.

**Core Philosophy:** Three pillars — Acquire, Curate, Experience

---

### Phase 0: Foundation & Rebranding

#### 0.1 Repository Changes
- Rename repository from `spotify-download` to `sonus`
- Update all internal references, documentation, and branding
- Preserve complete existing functionality from [1]:
  - Spotify OAuth integration
  - YouTube download with yt-dlp
  - Automatic playlist monitoring
  - Manual song requests
  - CSV import (Exportify format)
  - Docker self-hosting capability
  - PWA support

#### 0.2 Internationalization (i18n) Framework
Implement from day one:

| Aspect | Requirements |
|--------|-------------|
| Backend | Use `fastapi-babel` or similar; all user-facing strings externalized |
| Frontend | React-i18next with language detection |
| Default languages | English (en), German (de) |
| Storage | JSON translation files, lazy-loaded |
| Language switch | Persistent in user settings, detected from browser |

All new features must include both English and German translations before merge.

---

### Phase 1: Core Architecture Refactor (Weeks 1-2)

#### 1.1 Generic Track Model
Replace download-centric models with unified `Track` entity:

Track
├── id (UUID, internal)
├── sources[] (Spotify, YouTube Music, Apple Music, Upload, Manual)
│   ├── source_type: enum
│   ├── external_id
│   └── metadata_snapshot
├── files[] (physical files, multiple formats possible)
│   ├── path
│   ├── format (MP3, FLAC, WAV, OGG, OPUS, AAC, M4A)
│   ├── bitrate
│   ├── size_bytes
│   └── is_primary (for playback)
├── metadata (normalized)
│   ├── title, artists[], album, year, genre, cover_art_url
│   ├── duration_ms, track_number, disc_number
│   └── lyrics (optional)
├── library_location
│   ├── virtual_path (for organization)
│   └── physical_base_path
└── created_at, updated_at, last_played_at, play_count


#### 1.2 Enhanced Format Support
Extend FFmpeg integration [1]:

| Feature | Implementation |
|---------|---------------|
| Download formats | Configurable: MP3, FLAC, WAV, OGG, OPUS, AAC, M4A |
| Quality presets | "Archive" (FLAC), "Balanced" (320k MP3), "Compact" (192k OP3), "Mobile" (128k AAC) |
| Upload handling | Accept all listed formats; convert if needed or keep original |
| Format storage | Multiple formats per track allowed (keep FLAC + create MP3) |

#### 1.3 Preservation Requirements
- All existing API endpoints must remain functional at `/api/v1/legacy/*` OR with backward-compatible responses
- Existing `.env` configurations must remain valid
- Database migration must preserve all existing data

---

### Phase 2: Library Management (Weeks 3-5)

#### 2.1 File Manager Interface

**Backend:**
- Recursive directory scanning with inotify/watchdog (configurable)
- Background task: `library_scan` with progress tracking
- Hash-based duplicate detection (audio fingerprinting using chromaprint)

**Frontend (new views):**

| View | Function |
|------|----------|
| `/library` | Grid/list toggle, sortable columns, quick filter |
| `/library/folders` | Tree navigation, breadcrumb, drag-drop between folders |
| `/library/bulk` | Multi-select mode with floating action bar |

#### 2.2 Metadata & Organization Tools

**Individual track editing:**
- Inline metadata editor (title, artist, album, year, genre, track number)
- Cover art upload/replace (with automatic resizing)
- "Move to folder" and "Add to playlist" actions

**Bulk operations (critical):**
| Operation | UI Pattern |
|-----------|-----------|
| Rename | Template builder with live preview: `{artist} - {title}`, `{album}/{artist} - {title}`, `{year}/{genre}/{artist} - {title}`, etc. |
| Reorganize | Virtual folder structure → apply to filesystem (with confirmation) |
| Convert | Select target format(s), quality, keep/delete original |
| Compress | FLAC→MP3 for mobile collections, with "archive original" option |
| Delete | Move to trash (30-day grace period, restorable) |

**Template variables for all naming:** `artist`, `artists`, `title`, `album`, `year`, `genre`, `track_number`, `disc_number`, `album_artist`

#### 2.3 Duplicate Management
- Detection: Audio fingerprint (chroma-print) + duration + file size heuristics
- UI: "Potential duplicates" review queue
- Actions: Merge metadata, keep both, delete one, mark as different

---

### Phase 3: Multi-Source Expansion (Weeks 6-8)

#### 3.1 Source Architecture
Unified abstraction:


SourceProvider (abstract)
├── authenticate() → OAuth flow or API key
├── get_playlists() → list with metadata
├── get_playlist_tracks(playlist_id)
├── get_liked_songs()
├── search(query)
└── sync_to_library() → creates Track entries, queues downloads


Implementations:

| Source | Priority | Notes |
|--------|----------|-------|
| Spotify | Existing [1] | Refactor to SourceProvider pattern |
| YouTube Music | High | Use yt-dlp YTM support, OAuth similar complexity to Spotify |
| Apple Music | Medium | Metadata/playlist sync only (API limits); manual file upload for owned music |
| Local files | Existing [1] | Enhance with better metadata extraction |
| Manual entry | New | For vinyl rips, Bandcamp downloads, etc. |

#### 3.2 YouTube Music Implementation
Mirror Spotify functionality:

- OAuth 2.0 flow (separate from YouTube main)
- Playlist monitoring with hourly sync
- "Liked songs" sync
- Artist/album subscription (monitor for new releases)

#### 3.3 Apple Music Strategy
Research required: Evaluate MusicKit JS capabilities vs. unofficial APIs. **Decision point:**

- **Option A (Safe):** Playlist export via MusicKit → CSV → import to Sonus. Metadata only, manual file association.
- **Option B (Full):** Evaluate third-party libraries for download capability. Only proceed if stable and legally clear.

Default to Option A unless explicitly approved.

---

### Phase 4: Playback & Streaming (Weeks 9-11)

#### 4.1 Web Player

**Core features:**
- Persistent bottom player bar (mini) / full-screen view
- Queue management: play next, add to queue, clear, save as playlist
- Gapless playback (crossfade configurable: 0-5s)
- Keyboard shortcuts (space: play/pause, arrows: seek/volume, J/K: prev/next)
- Lyrics display (LRCParser or similar, sync if available)

**Audio handling:**
- Transcoding on-the-fly for bandwidth-limited scenarios (configurable)
- Direct file serving for local network
- Adaptive: FLAC for local, 320k MP3 for remote (configurable)

#### 4.2 Subsonic API Emulation
Implement `/rest/` endpoints for compatibility:

| Endpoint | Purpose |
|----------|---------|
| `ping.view` | Connection test |
| `getIndexes.view` | Artists/folders |
| `getMusicDirectory.view` | Albums/tracks in folder |
| `getAlbumList.view` | Recently added, etc. |
| `stream.view` | Audio streaming (transcode if needed) |
| `getPlaylists.view` / `getPlaylist.view` | Playlist sync |

Enables use with: DSub, Symfonium, play:Sub, Amperfy, etc.

#### 4.3 PWA Enhancements [1]
- Background audio playback (service worker)
- Media session API integration (lock screen controls)
- Offline playback: cache recently played, explicit "download for offline"

---

### Phase 5: Import/Export Generalization (Week 12)

#### 5.1 Unified Sources Section
Navigation: **Sources** → subsections:

| Subsection | Content |
|------------|---------|
| Spotify | OAuth status, monitored playlists, "Import from Exportify CSV" |
| YouTube Music | OAuth status, monitored playlists, liked songs sync |
| Apple Music | Connection status, CSV import instructions |
| Generic CSV | Universal importer (see below) |

#### 5.2 Universal CSV Importer

**Mapping UI:**
1. User uploads any CSV
2. Preview first 5 rows
3. Column mapping: "This column contains..." → `title`, `artist`, `album`, `isrc`, `duration`, `url` (optional), etc.
4. Validation: show how many rows are mappable
5. Import: create Track entries (pending download) or library entries (if files exist)

**Presets:** Spotify Exportify, YouTube Music Takeout, Apple Music library export, Last.fm history, custom.

---

### Phase 6: Polish & Extended Features (Ongoing)

#### 6.1 Smart Features (Recommended Additions)

| Feature | Description | Priority |
|---------|-------------|----------|
| Smart playlists | Auto-generated based on rules: "Unplayed for 30 days", "Added last 7 days", "Genre = Jazz AND Year < 1980" | Medium |
| Statistics dashboard | Listening history, top tracks/artists, library growth over time | Low |
| Webhooks/API | Outgoing notifications for new downloads, completed conversions | Low |
| Multi-user support | Optional: separate libraries per user, or shared library with personal playlists | Future |

#### 6.2 Technical Debt & Quality
- Comprehensive test coverage: pytest for backend, React Testing Library for frontend
- API documentation: OpenAPI/Swagger with examples
- Performance: database indexing, lazy loading for large libraries (>10k tracks)

---

## Technical Stack (Preserved & Extended)

From [1], maintain and extend:

| Layer | Current | Extensions |
|-------|---------|------------|
| Backend | Python, FastAPI, SQLModel | Add: celery (background tasks), chromaprint (audio fingerprint), babel (i18n) |
| Frontend | React, TypeScript, TailwindCSS, React Router | Add: react-i18next, @tanstack/react-query (server state), zustand (client state) |
| Database | SQLite | Consider: PostgreSQL option for multi-user/large libraries |
| Container | Docker, Docker Compose | Multi-arch builds, health checks |
| Audio | yt-dlp, FFmpeg | Add: chromaprint/fpcalc for fingerprinting |

---

## UI/UX Guidelines

### Navigation Structure

┌─────────────────────────────────────────┐
│  Sonus  │ Library │ Sources │ Player  │  [Search]  [Lang: EN/DE]  [User]
├─────────────────────────────────────────┤
│                                         │
│  [Context-aware main content]           │
│                                         │
│  [Persistent mini player when active]   │
│                                         │
└─────────────────────────────────────────┘

### Language Requirements
Every user-facing string must:
- Exist in `en.json` and `de.json`
- Use ICU MessageFormat for pluralization, dates, numbers
- Support RTL layouts (future-proofing, even if not immediate)

---

## Database Migration Strategy

1. Create new tables alongside existing
2. Backfill from existing data
3. Switch reads to new tables
4. Drop old tables in major version bump

Provide `sonus migrate` CLI command for manual trigger, automatic on container start.

---

## Success Criteria

| Phase | Deliverable | Verification |
|-------|-------------|------------|
| 0 | Sonus rebranded, i18n framework | All UI elements toggle EN/DE |
| 1 | Generic Track model, format flexibility | FLAC upload converts and plays; existing MP3 flows unchanged |
| 2 | File manager, bulk operations, duplicates | 1000+ track library navigable, renamed, reorganized |
| 3 | YouTube Music parity with Spotify | OAuth works, playlists sync hourly |
| 4 | Web player functional, Subsonic API | Music plays in browser; DSub connects and streams |
| 5 | Universal CSV import | Spotify, YTM, Apple, generic CSVs all importable |
| 6 | Smart playlists, stats | Rules-based playlists auto-update |

---

## Questions for Clarification (Answer Before Phase 3)

1. **Apple Music**: Proceed with metadata-only (Option A) or investigate full integration (Option B)?
2. **Database**: Stay with SQLite or add PostgreSQL option for scalability?
3. **Multi-format storage**: Keep converted files alongside originals (more disk) or replace (destructive)?
4. **Multi-user**: Required for MVP, or single-user with potential future extension?
5. **Mobile apps**: Native apps desired, or PWA-only sufficient?
6. **Lyrics sources**: Licensed API (MusixMatch, Genius) or open (LRCLIB)?

---

## Reference

[1] LStoneyy. *spotify-download: Self-hosted Docker Compose service with React web UI for Spotify playlist downloading and monitoring.* GitHub. https://github.com/LStoneyy/spotify-download

