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
  last_poll: string | null;
  next_poll: string | null;
  total_done: number;
  total_failed: number;
  total_skipped: number;
  queue_length: number;
}

export interface Settings {
  id: number;
  playlist_url: string | null;
  quality: string;
  poll_interval_minutes: number;
  file_template: string;
  sleep_between_downloads: number;
  max_retries: number;
}

export interface SpotifyStatus {
  connected: boolean;
  expires_at: number | null;
}

export interface SyncResult {
  ok?: boolean;
  error?: string;
  total_found?: number;
  added?: number;
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

export const triggerSync = () =>
  apiFetch<SyncResult>("/sync", { method: "POST" });

export const createRequest = (query: string) =>
  apiFetch<Track>("/requests", {
    method: "POST",
    body: JSON.stringify({ query }),
  });

export const getSpotifyStatus = () => apiFetch<SpotifyStatus>("/spotify/status");
export const disconnectSpotify = () =>
  apiFetch<{ disconnected: boolean }>("/spotify/disconnect", { method: "DELETE" });

export const getSettings = () => apiFetch<Settings>("/settings");

export const updateSettings = (body: Partial<Omit<Settings, "id">>) =>
  apiFetch<Settings>("/settings", {
    method: "PUT",
    body: JSON.stringify(body),
  });
