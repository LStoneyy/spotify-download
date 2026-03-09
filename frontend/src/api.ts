// Centralised API helpers
// When running in Docker, nginx proxies /api → backend. In dev, Vite proxies it.

const BASE = "/api";

async function apiFetch<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...opts?.headers },
    ...opts,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status} ${text}`);
  }
  return res.json() as Promise<T>;
}

// ── Types ────────────────────────────────────────────────────────────────────

export interface Track {
  id: number;
  spotify_id: string | null;
  title: string;
  artist: string | null;
  album: string | null;
  status: "queued" | "downloading" | "done" | "failed" | "skipped";
  file_path: string | null;
  error_msg: string | null;
  source: "playlist" | "manual";
  requested_at: string;
  downloaded_at: string | null;
}

export interface DownloadsResponse {
  items: Track[];
  total: number;
  page: number;
  limit: number;
}

export interface StatusResponse {
  currently_downloading: { track_id: number; title: string; artist: string | null } | null;
  total_done: number;
  total_failed: number;
  total_skipped: number;
  queue_length: number;
}

export interface Settings {
  id: number;
  quality: string;
  file_template: string;
  sleep_between_downloads: number;
  max_retries: number;
}

export interface ImportResult {
  ok: boolean;
  total: number;
  imported: number;
  skipped: number;
}

export interface MonitoredPlaylist {
  id: number;
  spotify_id: string;
  name: string | null;
  url: string;
  track_count: number;
  last_synced_at: string | null;
  sync_error: string | null;
  created_at: string;
}

export interface SyncResult {
  playlist_id: number;
  new_tracks: number;
  total_tracks: number;
  error: string | null;
}

export interface AuthStatus {
  authenticated: boolean;
  expires_at: number | null;
}

export const getDownloads = (params?: {
  page?: number;
  limit?: number;
  status?: string;
  source?: string;
}) => {
  const qs = new URLSearchParams();
  if (params?.page) qs.set("page", String(params.page));
  if (params?.limit) qs.set("limit", String(params.limit));
  if (params?.status) qs.set("status", params.status);
  if (params?.source) qs.set("source", params.source);
  return apiFetch<DownloadsResponse>(`/downloads?${qs}`);
};

export const getStatus = () => apiFetch<StatusResponse>("/status");

export const createRequest = (query: string) =>
  apiFetch<Track>("/requests", {
    method: "POST",
    body: JSON.stringify({ query }),
  });

export const getSettings = () => apiFetch<Settings>("/settings");

export const updateSettings = (body: Partial<Omit<Settings, "id">>) =>
  apiFetch<Settings>("/settings", {
    method: "PUT",
    body: JSON.stringify(body),
  });

/** Upload a CSV file and queue its tracks for download. */
export const importCsv = async (file: File): Promise<ImportResult> => {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}/import/csv`, { method: "POST", body: form });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status} ${text}`);
  }
  return res.json() as Promise<ImportResult>;
};

export const getPlaylists = () => apiFetch<MonitoredPlaylist[]>("/playlists");

export const addPlaylist = (url: string) =>
  apiFetch<MonitoredPlaylist>("/playlists", {
    method: "POST",
    body: JSON.stringify({ url }),
  });

export const deletePlaylist = (id: number) =>
  apiFetch<{ ok: boolean }>("/playlists/" + id, { method: "DELETE" });

export const syncPlaylist = (id: number) =>
  apiFetch<SyncResult>("/playlists/" + id + "/sync", { method: "POST" });

export const getAuthStatus = () => apiFetch<AuthStatus>("/auth/status");

export const login = () => { window.location.href = "/api/auth/login"; };

export const logout = () => apiFetch<{ ok: boolean }>("/auth/logout", { method: "POST" });

export interface UploadResult {
  ok: boolean;
  file_path: string;
  message?: string;
}

export const uploadFile = async (
  file: File,
  title: string,
  artist: string,
  album?: string
): Promise<UploadResult> => {
  const form = new FormData();
  form.append("file", file);
  form.append("title", title);
  form.append("artist", artist);
  if (album) {
    form.append("album", album);
  }
  const res = await fetch(`${BASE}/upload`, { method: "POST", body: form });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status} ${text}`);
  }
  return res.json() as Promise<UploadResult>;
};
