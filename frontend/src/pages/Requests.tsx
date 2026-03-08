import { useEffect, useState } from "react";
import { createRequest, getDownloads, type Track } from "../api";

const STATUS_COLORS: Record<Track["status"], string> = {
  done:        "bg-ctp-green/20 text-ctp-green border-ctp-green/30",
  queued:      "bg-ctp-yellow/20 text-ctp-yellow border-ctp-yellow/30",
  downloading: "bg-ctp-blue/20 text-ctp-blue border-ctp-blue/30",
  failed:      "bg-ctp-red/20 text-ctp-red border-ctp-red/30",
  skipped:     "bg-ctp-overlay0/20 text-ctp-subtext0 border-ctp-overlay0/30",
};

export default function Requests() {
  const [query, setQuery] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [manualTracks, setManualTracks] = useState<Track[]>([]);

  const fetchManual = async () => {
    const data = await getDownloads({ source: "manual", limit: 50 }).catch(() => null);
    if (data) setManualTracks(data.items);
  };

  useEffect(() => {
    fetchManual();
    const id = setInterval(fetchManual, 5000);
    return () => clearInterval(id);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const q = query.trim();
    if (!q) return;
    setSubmitting(true);
    setError("");
    setSuccess("");
    try {
      const track = await createRequest(q);
      setSuccess(`Queued: ${track.artist ? `${track.artist} – ` : ""}${track.title}`);
      setQuery("");
      fetchManual();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setSubmitting(false);
      setTimeout(() => setSuccess(""), 4000);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h2 className="text-xl font-bold text-ctp-text">Request a Song</h2>

      {/* Request form */}
      <div className="bg-ctp-mantle rounded-xl p-5 border border-ctp-surface0">
        <p className="text-sm text-ctp-subtext0 mb-4">
          Enter a song name or <span className="text-ctp-text font-medium">Artist – Title</span> to
          queue a download not in your playlist.
        </p>
        <form onSubmit={handleSubmit} className="flex gap-2 flex-col sm:flex-row">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. The Weeknd – Blinding Lights"
            className="flex-1 bg-ctp-surface0 border border-ctp-surface1 rounded-lg px-4 py-2.5 text-sm text-ctp-text placeholder-ctp-overlay0 focus:outline-none focus:border-ctp-blue transition-colors"
          />
          <button
            type="submit"
            disabled={submitting || !query.trim()}
            className="px-5 py-2.5 rounded-lg bg-ctp-green text-ctp-base text-sm font-semibold hover:bg-ctp-teal disabled:opacity-50 transition-colors whitespace-nowrap"
          >
            {submitting ? "Queuing…" : "Add to queue"}
          </button>
        </form>
        {error && <p className="mt-3 text-sm text-ctp-red">{error}</p>}
        {success && <p className="mt-3 text-sm text-ctp-green">✓ {success}</p>}
      </div>

      {/* Manual request history */}
      <div>
        <h3 className="text-sm font-semibold text-ctp-subtext0 uppercase tracking-wide mb-3">
          Manual requests
        </h3>
        {manualTracks.length === 0 ? (
          <p className="text-ctp-overlay0 text-sm py-6 text-center bg-ctp-mantle rounded-xl border border-ctp-surface0">
            No manual requests yet.
          </p>
        ) : (
          <div className="space-y-2">
            {manualTracks.map((t) => (
              <div
                key={t.id}
                className="bg-ctp-mantle rounded-xl px-4 py-3 border border-ctp-surface0 flex items-center gap-3"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{t.title}</p>
                  {t.artist && (
                    <p className="text-xs text-ctp-subtext0 truncate">{t.artist}</p>
                  )}
                  {t.error_msg && (
                    <p className="text-xs text-ctp-red mt-0.5 truncate">{t.error_msg}</p>
                  )}
                </div>
                <span
                  className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border flex-shrink-0 ${STATUS_COLORS[t.status]}`}
                >
                  {t.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
