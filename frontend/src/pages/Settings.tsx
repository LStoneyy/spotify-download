import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { getSettings, updateSettings, getSpotifyStatus, disconnectSpotify, type Settings, type SpotifyStatus } from "../api";

const QUALITIES = ["128", "192", "256", "320"];

function previewFilename(template: string): string {
  return (
    template
      .replace("{artist}", "The Weeknd")
      .replace("{title}", "Blinding Lights")
      .replace("{album}", "After Hours") + ".mp3"
  );
}

export default function SettingsPage() {
  const [form, setForm] = useState<Partial<Settings>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");
  const [spotifyStatus, setSpotifyStatus] = useState<SpotifyStatus | null>(null);
  const [disconnecting, setDisconnecting] = useState(false);
  const [searchParams, setSearchParams] = useSearchParams();

  const spotifyConnected = searchParams.get("spotify_connected") === "1";
  const spotifyError = searchParams.get("spotify_error");

  // Clear query params from URL without re-rendering (cosmetic)
  useEffect(() => {
    if (spotifyConnected || spotifyError) {
      setSearchParams({}, { replace: true });
    }
  }, []);

  useEffect(() => {
    Promise.all([
      getSettings().then((s) => setForm(s)),
      getSpotifyStatus().then((s) => setSpotifyStatus(s)),
    ])
      .catch(() => setError("Failed to load settings."))
      .finally(() => setLoading(false));
  }, []);

  const handleDisconnect = async () => {
    setDisconnecting(true);
    try {
      await disconnectSpotify();
      setSpotifyStatus({ connected: false, expires_at: null });
    } finally {
      setDisconnecting(false);
    }
  };

  const set = <K extends keyof Settings>(key: K, value: Settings[K]) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  const handleSave = async () => {
    setSaving(true);
    setError("");
    try {
      const updated = await updateSettings(form);
      setForm(updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Save failed.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-40 text-ctp-subtext0">Loading…</div>
    );
  }

  const pollMinutes = form.poll_interval_minutes ?? 60;
  const sleepSec = form.sleep_between_downloads ?? 7;

  return (
    <div className="max-w-xl mx-auto space-y-6">
      <h2 className="text-xl font-bold text-ctp-text">Settings</h2>

      {/* OAuth result banners */}
      {spotifyConnected && (
        <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-ctp-green/10 border border-ctp-green/30 text-ctp-green text-sm">
          <span>✓</span> Spotify account connected successfully!
        </div>
      )}
      {spotifyError && (
        <div className="px-4 py-3 rounded-xl bg-ctp-red/10 border border-ctp-red/30 text-ctp-red text-sm">
          Spotify auth error: {spotifyError}
        </div>
      )}

      {/* Spotify */}
      <section className="bg-ctp-mantle rounded-xl p-5 border border-ctp-surface0 space-y-4">
        <h3 className="text-sm font-semibold text-ctp-blue uppercase tracking-wide">Spotify</h3>

        {/* Account connection */}
        <div className="space-y-2">
          <label className="text-xs font-medium text-ctp-subtext0">Account</label>
          {spotifyStatus?.connected ? (
            <div className="flex items-center justify-between gap-3 bg-ctp-green/10 border border-ctp-green/30 rounded-lg px-4 py-3">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-ctp-green inline-block"></span>
                <span className="text-sm text-ctp-green font-medium">Connected</span>
              </div>
              <button
                onClick={handleDisconnect}
                disabled={disconnecting}
                className="text-xs text-ctp-subtext0 hover:text-ctp-red transition-colors disabled:opacity-50"
              >
                {disconnecting ? "Disconnecting…" : "Disconnect"}
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              <div className="flex items-center gap-2 bg-ctp-red/10 border border-ctp-red/30 rounded-lg px-4 py-3">
                <span className="w-2 h-2 rounded-full bg-ctp-red inline-block"></span>
                <span className="text-sm text-ctp-red font-medium">Not connected</span>
              </div>
              <a
                href="/api/spotify/auth"
                className="block w-full py-2.5 rounded-lg bg-ctp-green text-ctp-base text-sm font-bold text-center hover:bg-ctp-teal transition-colors"
              >
                Connect Spotify Account
              </a>
              <p className="text-xs text-ctp-overlay0">
                Required for playlist sync. Make sure{" "}
                <code className="text-ctp-yellow">http://127.0.0.1:6767/api/spotify/callback</code>{" "}
                is listed as a Redirect URI in your{" "}
                <a href="https://developer.spotify.com/dashboard" target="_blank" rel="noopener noreferrer" className="text-ctp-blue underline">Spotify app</a>.
              </p>
            </div>
          )}
        </div>

        <div className="space-y-1">
          <label className="text-xs font-medium text-ctp-subtext0">Playlist URL</label>
          <input
            type="url"
            value={form.playlist_url ?? ""}
            onChange={(e) => set("playlist_url", e.target.value)}
            placeholder="https://open.spotify.com/playlist/…"
            className="w-full bg-ctp-surface0 border border-ctp-surface1 rounded-lg px-3 py-2 text-sm text-ctp-text placeholder-ctp-overlay0 focus:outline-none focus:border-ctp-blue transition-colors"
          />
          <p className="text-xs text-ctp-overlay0">Paste your playlist URL here.</p>
        </div>

        <div className="space-y-1">
          <label className="text-xs font-medium text-ctp-subtext0">
            Poll interval: <span className="text-ctp-text font-bold">{pollMinutes} min</span>
          </label>
          <input
            type="range"
            min={15}
            max={1440}
            step={15}
            value={pollMinutes}
            onChange={(e) => set("poll_interval_minutes", parseInt(e.target.value))}
            className="w-full accent-ctp-blue"
          />
          <div className="flex justify-between text-xs text-ctp-overlay0">
            <span>15 min</span>
            <span>24 h</span>
          </div>
        </div>
      </section>

      {/* Downloads */}
      <section className="bg-ctp-mantle rounded-xl p-5 border border-ctp-surface0 space-y-4">
        <h3 className="text-sm font-semibold text-ctp-peach uppercase tracking-wide">Downloads</h3>

        {/* Quality */}
        <div className="space-y-1">
          <label className="text-xs font-medium text-ctp-subtext0">MP3 Quality</label>
          <div className="flex gap-2">
            {QUALITIES.map((q) => (
              <button
                key={q}
                onClick={() => set("quality", q)}
                className={`flex-1 py-2 rounded-lg text-sm font-semibold border transition-colors ${
                  form.quality === q
                    ? "bg-ctp-green/20 text-ctp-green border-ctp-green/40"
                    : "bg-ctp-surface0 text-ctp-subtext0 border-ctp-surface1 hover:border-ctp-overlay0"
                }`}
              >
                {q}
              </button>
            ))}
          </div>
        </div>

        {/* Sleep */}
        <div className="space-y-1">
          <label className="text-xs font-medium text-ctp-subtext0">
            Sleep between downloads:{" "}
            <span className="text-ctp-text font-bold">{sleepSec}s</span>
          </label>
          <input
            type="range"
            min={3}
            max={30}
            step={1}
            value={sleepSec}
            onChange={(e) => set("sleep_between_downloads", parseInt(e.target.value))}
            className="w-full accent-ctp-peach"
          />
          <p className="text-xs text-ctp-overlay0">
            YouTube rate-limits guests at ~300 tracks/hour. 5–10s is recommended.
          </p>
        </div>

        {/* Retries */}
        <div className="space-y-1">
          <label className="text-xs font-medium text-ctp-subtext0">Max retries per track</label>
          <input
            type="number"
            min={1}
            max={10}
            value={form.max_retries ?? 3}
            onChange={(e) => set("max_retries", parseInt(e.target.value))}
            className="w-24 bg-ctp-surface0 border border-ctp-surface1 rounded-lg px-3 py-2 text-sm text-ctp-text focus:outline-none focus:border-ctp-blue transition-colors"
          />
        </div>
      </section>

      {/* File naming */}
      <section className="bg-ctp-mantle rounded-xl p-5 border border-ctp-surface0 space-y-4">
        <h3 className="text-sm font-semibold text-ctp-mauve uppercase tracking-wide">File naming</h3>

        <div className="space-y-1">
          <label className="text-xs font-medium text-ctp-subtext0">Template</label>
          <input
            type="text"
            value={form.file_template ?? "{artist} - {title}"}
            onChange={(e) => set("file_template", e.target.value)}
            className="w-full bg-ctp-surface0 border border-ctp-surface1 rounded-lg px-3 py-2 text-sm text-ctp-text placeholder-ctp-overlay0 font-mono focus:outline-none focus:border-ctp-blue transition-colors"
          />
          <p className="text-xs text-ctp-overlay0">
            Variables: <code className="text-ctp-mauve">{"{artist}"}</code>{" "}
            <code className="text-ctp-mauve">{"{title}"}</code>{" "}
            <code className="text-ctp-mauve">{"{album}"}</code>
          </p>
        </div>

        {/* Live preview */}
        <div className="bg-ctp-surface0 rounded-lg px-4 py-3">
          <p className="text-xs text-ctp-subtext0 mb-1 font-medium">Preview</p>
          <p className="text-sm text-ctp-text font-mono truncate">
            {previewFilename(form.file_template ?? "{artist} - {title}")}
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          {[
            "{artist} - {title}",
            "{title}",
            "{album}/{artist} - {title}",
          ].map((preset) => (
            <button
              key={preset}
              onClick={() => set("file_template", preset)}
              className="px-3 py-1 text-xs rounded-full bg-ctp-surface0 text-ctp-subtext0 border border-ctp-surface1 hover:border-ctp-overlay0 hover:text-ctp-text transition-colors font-mono"
            >
              {preset}
            </button>
          ))}
        </div>
      </section>

      {/* Cookies hint */}
      <section className="bg-ctp-surface0/50 rounded-xl p-4 border border-ctp-surface0 text-xs text-ctp-subtext0 space-y-1">
        <p className="font-semibold text-ctp-text">Optional: YouTube Cookies</p>
        <p>
          Mount a <code className="text-ctp-yellow">cookies.txt</code> file (Netscape format) inside
          the container at <code className="text-ctp-yellow">/data/cookies.txt</code> to improve
          download reliability, especially for rate-limited sessions.
        </p>
        <p>Add to your compose file under <code className="text-ctp-yellow">backend → volumes</code>:</p>
        <pre className="bg-ctp-mantle rounded-lg p-2 text-ctp-text text-xs mt-1 overflow-x-auto">
          {`- /path/to/cookies.txt:/data/cookies.txt:ro`}
        </pre>
      </section>

      {/* Error / save */}
      {error && <p className="text-sm text-ctp-red">{error}</p>}
      <button
        onClick={handleSave}
        disabled={saving}
        className="w-full py-3 rounded-xl bg-ctp-blue text-ctp-base font-bold text-sm hover:bg-ctp-sapphire disabled:opacity-50 transition-colors"
      >
        {saving ? "Saving…" : saved ? "✓ Saved!" : "Save settings"}
      </button>
    </div>
  );
}
