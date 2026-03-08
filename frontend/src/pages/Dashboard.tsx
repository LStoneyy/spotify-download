import { useEffect, useState, useCallback } from "react";
import {
  getDownloads,
  getStatus,
  triggerSync,
  type DownloadsResponse,
  type StatusResponse,
  type Track,
} from "../api";
import StatusBar from "../components/StatusBar";

const STATUS_COLORS: Record<Track["status"], string> = {
  done:        "bg-ctp-green/20 text-ctp-green border-ctp-green/30",
  queued:      "bg-ctp-yellow/20 text-ctp-yellow border-ctp-yellow/30",
  downloading: "bg-ctp-blue/20 text-ctp-blue border-ctp-blue/30",
  failed:      "bg-ctp-red/20 text-ctp-red border-ctp-red/30",
  skipped:     "bg-ctp-overlay0/20 text-ctp-subtext0 border-ctp-overlay0/30",
};

function StatusBadge({ status }: { status: Track["status"] }) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${STATUS_COLORS[status]}`}
    >
      {status}
    </span>
  );
}

function StatCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="bg-ctp-surface0 rounded-xl p-4 flex flex-col gap-1">
      <p className="text-xs text-ctp-subtext0 font-medium uppercase tracking-wide">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
    </div>
  );
}

function fmtRelative(iso: string | null): string {
  if (!iso) return "–";
  const diff = Math.floor((Date.now() - new Date(iso + (iso.endsWith("Z") ? "" : "Z")).getTime()) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

function fmtAbs(iso: string | null): string {
  if (!iso) return "–";
  return new Date(iso + (iso.endsWith("Z") ? "" : "Z")).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function Dashboard() {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [data, setData] = useState<DownloadsResponse | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>("");
  const [page, setPage] = useState(1);
  const [syncing, setSyncing] = useState(false);
  const [syncMsg, setSyncMsg] = useState("");

  const fetchAll = useCallback(async () => {
    const [s, d] = await Promise.all([
      getStatus().catch(() => null),
      getDownloads({ page, limit: 50, status: filterStatus || undefined }).catch(() => null),
    ]);
    if (s) setStatus(s);
    if (d) setData(d);
  }, [page, filterStatus]);

  useEffect(() => {
    fetchAll();
    const id = setInterval(fetchAll, 5000);
    return () => clearInterval(id);
  }, [fetchAll]);

  const handleSync = async () => {
    setSyncing(true);
    setSyncMsg("");
    try {
      await triggerSync();
      setSyncMsg("Sync triggered!");
    } catch {
      setSyncMsg("Failed to sync.");
    } finally {
      setSyncing(false);
      setTimeout(() => setSyncMsg(""), 3000);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <h2 className="text-xl font-bold text-ctp-text">Dashboard</h2>
        <div className="flex items-center gap-2">
          {syncMsg && (
            <span className="text-xs text-ctp-green">{syncMsg}</span>
          )}
          <button
            onClick={handleSync}
            disabled={syncing}
            className="px-4 py-2 rounded-lg bg-ctp-blue text-ctp-base text-sm font-semibold hover:bg-ctp-sapphire disabled:opacity-50 transition-colors"
          >
            {syncing ? "Syncing…" : "🔄 Sync Now"}
          </button>
        </div>
      </div>

      {/* Currently downloading */}
      <StatusBar status={status} />

      {/* Stats */}
      {status && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatCard label="Downloaded" value={status.total_done} color="text-ctp-green" />
          <StatCard label="Queued" value={status.queue_length} color="text-ctp-yellow" />
          <StatCard label="Failed" value={status.total_failed} color="text-ctp-red" />
          <StatCard label="Skipped" value={status.total_skipped} color="text-ctp-subtext0" />
        </div>
      )}

      {/* Poll info */}
      {status && (
        <div className="flex flex-wrap gap-4 text-xs text-ctp-subtext0">
          <span>Last sync: <span className="text-ctp-text">{fmtRelative(status.last_poll)}</span></span>
          <span>Next sync: <span className="text-ctp-text">{fmtAbs(status.next_poll)}</span></span>
        </div>
      )}

      {/* Filter bar */}
      <div className="flex gap-2 flex-wrap">
        {["", "done", "queued", "downloading", "failed", "skipped"].map((s) => (
          <button
            key={s}
            onClick={() => { setFilterStatus(s); setPage(1); }}
            className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
              filterStatus === s
                ? "bg-ctp-blue/20 text-ctp-blue border-ctp-blue/40"
                : "border-ctp-surface1 text-ctp-subtext0 hover:border-ctp-overlay0"
            }`}
          >
            {s === "" ? "All" : s}
          </button>
        ))}
      </div>

      {/* ── Desktop table ──────────────────────────────────────────────── */}
      <div className="hidden md:block bg-ctp-mantle rounded-xl overflow-hidden border border-ctp-surface0">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-ctp-surface0 text-left text-xs text-ctp-subtext0 uppercase tracking-wide">
              <th className="px-4 py-3 font-medium">Track</th>
              <th className="px-4 py-3 font-medium">Source</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Time</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ctp-surface0">
            {data?.items.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-ctp-subtext0">
                  No tracks yet.
                </td>
              </tr>
            )}
            {data?.items.map((t) => (
              <tr key={t.id} className="hover:bg-ctp-surface0/40 transition-colors">
                <td className="px-4 py-3 max-w-xs">
                  <p className="font-medium truncate">{t.title}</p>
                  {t.artist && (
                    <p className="text-xs text-ctp-subtext0 truncate">{t.artist}</p>
                  )}
                  {t.error_msg && (
                    <p className="text-xs text-ctp-red mt-0.5 truncate">{t.error_msg}</p>
                  )}
                </td>
                <td className="px-4 py-3">
                  <span className="text-xs text-ctp-subtext0">{t.source}</span>
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={t.status} />
                </td>
                <td className="px-4 py-3 text-xs text-ctp-subtext0 whitespace-nowrap">
                  {fmtRelative(t.downloaded_at || t.requested_at)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* ── Mobile card list ───────────────────────────────────────────── */}
      <div className="md:hidden space-y-2">
        {data?.items.length === 0 && (
          <div className="text-center text-ctp-subtext0 py-10">No tracks yet.</div>
        )}
        {data?.items.map((t) => (
          <div key={t.id} className="bg-ctp-mantle rounded-xl p-4 border border-ctp-surface0">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0 flex-1">
                <p className="font-semibold truncate text-sm">{t.title}</p>
                {t.artist && (
                  <p className="text-xs text-ctp-subtext0 truncate">{t.artist}</p>
                )}
                {t.error_msg && (
                  <p className="text-xs text-ctp-red mt-0.5 line-clamp-2">{t.error_msg}</p>
                )}
              </div>
              <StatusBadge status={t.status} />
            </div>
            <div className="flex items-center gap-3 mt-2 text-xs text-ctp-overlay0">
              <span>{t.source}</span>
              <span>·</span>
              <span>{fmtRelative(t.downloaded_at || t.requested_at)}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Pagination */}
      {data && data.total > data.limit && (
        <div className="flex items-center justify-between text-sm">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-1.5 rounded-lg bg-ctp-surface0 text-ctp-text disabled:opacity-40 hover:bg-ctp-surface1 transition-colors"
          >
            ← Prev
          </button>
          <span className="text-ctp-subtext0 text-xs">
            Page {page} · {data.total} total
          </span>
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={page * data.limit >= data.total}
            className="px-3 py-1.5 rounded-lg bg-ctp-surface0 text-ctp-text disabled:opacity-40 hover:bg-ctp-surface1 transition-colors"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
