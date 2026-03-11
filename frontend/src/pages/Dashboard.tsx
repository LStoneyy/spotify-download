import { useEffect, useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import {
  getDownloads,
  getStatus,
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
  const { t } = useTranslation();
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${STATUS_COLORS[status]}`}
    >
      {t(`statusLabels.${status}`)}
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

function fmtRelative(iso: string | null, t: (key: string, options?: Record<string, unknown>) => string): string {
  if (!iso) return "–";
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (isNaN(diff)) return "–";
  if (diff < 60) return t("timeAgo.secondsAgo", { count: diff });
  if (diff < 3600) return t("timeAgo.minutesAgo", { count: Math.floor(diff / 60) });
  return t("timeAgo.hoursAgo", { count: Math.floor(diff / 3600) });
}

function fmtAbs(iso: string | null): string {
  if (!iso) return "–";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return "–";
  return d.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function Dashboard() {
  const { t } = useTranslation();
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [data, setData] = useState<DownloadsResponse | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>("");
  const [filterSource, setFilterSource] = useState<string>("");
  const [page, setPage] = useState(1);

  const fetchAll = useCallback(async () => {
    const [s, d] = await Promise.all([
      getStatus().catch(() => null),
      getDownloads({ page, limit: 50, status: filterStatus || undefined, source: filterSource || undefined }).catch(() => null),
    ]);
    if (s) setStatus(s);
    if (d) setData(d);
  }, [page, filterStatus, filterSource]);

  useEffect(() => {
    fetchAll();
    const id = setInterval(fetchAll, 5000);
    return () => clearInterval(id);
  }, [fetchAll]);

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <h2 className="text-xl font-bold text-ctp-text">{t("dashboard.title")}</h2>
      </div>

      {/* Currently downloading */}
      <StatusBar status={status} />

      {/* Stats */}
      {status && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatCard label={t("dashboard.downloaded")} value={status.total_done} color="text-ctp-green" />
          <StatCard label={t("dashboard.queued")} value={status.queue_length} color="text-ctp-yellow" />
          <StatCard label={t("dashboard.failed")} value={status.total_failed} color="text-ctp-red" />
          <StatCard label={t("dashboard.skipped")} value={status.total_skipped} color="text-ctp-subtext0" />
        </div>
      )}

      {/* Filter bar */}
      <div className="space-y-2">
        <div className="flex gap-2 flex-wrap">
          {[t("common.all"), t("common.playlist"), t("common.manual")].map((label, i) => {
            const val = i === 0 ? "" : i === 1 ? "playlist" : "manual";
            return (
              <button
                key={label}
                onClick={() => { setFilterSource(val); setPage(1); }}
                className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                  filterSource === val
                    ? "bg-ctp-mauve/20 text-ctp-mauve border-ctp-mauve/40"
                    : "border-ctp-surface1 text-ctp-subtext0 hover:border-ctp-overlay0"
                }`}
              >
                {label}
              </button>
            );
          })}
        </div>
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
              {s === "" ? t("dashboard.allStatuses") : t(`statusLabels.${s}`)}
            </button>
          ))}
        </div>
      </div>

      {/* ── Desktop table ──────────────────────────────────────────────── */}
      <div className="hidden md:block bg-ctp-mantle rounded-xl overflow-hidden border border-ctp-surface0">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-ctp-surface0 text-left text-xs text-ctp-subtext0 uppercase tracking-wide">
              <th className="px-4 py-3 font-medium">{t("dashboard.track")}</th>
              <th className="px-4 py-3 font-medium">{t("dashboard.source")}</th>
              <th className="px-4 py-3 font-medium">{t("dashboard.status")}</th>
              <th className="px-4 py-3 font-medium">{t("dashboard.time")}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ctp-surface0">
            {data?.items.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-ctp-subtext0">
                  {t("dashboard.noTracks")}
                </td>
              </tr>
            )}
            {data?.items.map((track) => (
              <tr key={track.id} className="hover:bg-ctp-surface0/40 transition-colors">
                <td className="px-4 py-3 max-w-xs">
                  <p className="font-medium truncate">{track.title}</p>
                  {track.artist && (
                    <p className="text-xs text-ctp-subtext0 truncate">{track.artist}</p>
                  )}
                  {track.error_msg && (
                    <p className="text-xs text-ctp-red mt-0.5 truncate">{track.error_msg}</p>
                  )}
                </td>
                <td className="px-4 py-3">
                  <span className="text-xs text-ctp-subtext0">{track.source}</span>
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={track.status} />
                </td>
                <td className="px-4 py-3 text-xs text-ctp-subtext0 whitespace-nowrap">
                  {fmtRelative(track.downloaded_at || track.requested_at, t)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* ── Mobile card list ───────────────────────────────────────────── */}
      <div className="md:hidden space-y-2">
        {data?.items.length === 0 && (
          <div className="text-center text-ctp-subtext0 py-10">{t("dashboard.noTracks")}</div>
        )}
        {data?.items.map((track) => (
          <div key={track.id} className="bg-ctp-mantle rounded-xl p-4 border border-ctp-surface0">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0 flex-1">
                <p className="font-semibold truncate text-sm">{track.title}</p>
                {track.artist && (
                  <p className="text-xs text-ctp-subtext0 truncate">{track.artist}</p>
                )}
                {track.error_msg && (
                  <p className="text-xs text-ctp-red mt-0.5 line-clamp-2">{track.error_msg}</p>
                )}
              </div>
              <StatusBadge status={track.status} />
            </div>
            <div className="flex items-center gap-3 mt-2 text-xs text-ctp-overlay0">
              <span>{track.source}</span>
              <span>·</span>
              <span>{fmtRelative(track.downloaded_at || track.requested_at, t)}</span>
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
            ← {t("dashboard.prev")}
          </button>
          <span className="text-ctp-subtext0 text-xs">
            {t("dashboard.page")} {page} · {data.total} {t("dashboard.total")}
          </span>
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={page * data.limit >= data.total}
            className="px-3 py-1.5 rounded-lg bg-ctp-surface0 text-ctp-text disabled:opacity-40 hover:bg-ctp-surface1 transition-colors"
          >
            {t("dashboard.next")} →
          </button>
        </div>
      )}
    </div>
  );
}