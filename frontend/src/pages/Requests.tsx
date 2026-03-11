import { useEffect, useState } from "react";
import { useTranslation, Trans } from "react-i18next";
import { createRequest, getDownloads, uploadFile, type Track } from "../api";
import UploadModal from "../components/UploadModal";

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

export default function Requests() {
  const { t } = useTranslation();
  const [query, setQuery] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [manualTracks, setManualTracks] = useState<Track[]>([]);
  const [showUploadModal, setShowUploadModal] = useState(false);

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
      setSuccess(`${t("requests.queuing")}: ${track.artist ? `${track.artist} – ` : ""}${track.title}`);
      setQuery("");
      fetchManual();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t("errors.failedToLoad"));
    } finally {
      setSubmitting(false);
      setTimeout(() => setSuccess(""), 4000);
    }
  };

  const handleUpload = async (file: File, title: string, artist: string, album: string) => {
    setError("");
    setSuccess("");
    try {
      const result = await uploadFile(file, title, artist, album);
      setSuccess(`${t("success.uploaded")}: ${artist} – ${title}`);
      fetchManual();
    } catch (err: unknown) {
      throw err;
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h2 className="text-xl font-bold text-ctp-text">{t("requests.title")}</h2>

      {/* Request form */}
      <div className="bg-ctp-mantle rounded-xl p-5 border border-ctp-surface0">
        <p className="text-sm text-ctp-subtext0 mb-4">
          <Trans i18nKey="requests.description" components={{ 1: <span className="text-ctp-text font-medium" /> }} />
        </p>
        <form onSubmit={handleSubmit} className="flex gap-2 flex-col sm:flex-row">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t("requests.placeholder")}
            className="flex-1 bg-ctp-surface0 border border-ctp-surface1 rounded-lg px-4 py-2.5 text-sm text-ctp-text placeholder-ctp-overlay0 focus:outline-none focus:border-ctp-blue transition-colors"
          />
          <button
            type="submit"
            disabled={submitting || !query.trim()}
            className="px-5 py-2.5 rounded-lg bg-ctp-green text-ctp-base text-sm font-semibold hover:bg-ctp-teal disabled:opacity-50 transition-colors whitespace-nowrap"
          >
            {submitting ? `${t("requests.queuing")}…` : t("requests.addToQueue")}
          </button>
        </form>
        {error && <p className="mt-3 text-sm text-ctp-red">{error}</p>}
        {success && <p className="mt-3 text-sm text-ctp-green">✓ {success}</p>}
      </div>

      {/* Upload button */}
      <div className="bg-ctp-mantle rounded-xl p-5 border border-ctp-surface0">
        <h3 className="text-sm font-semibold text-ctp-subtext0 uppercase tracking-wide mb-3">
          {t("requests.uploadFromComputer")}
        </h3>
        <button
          onClick={() => setShowUploadModal(true)}
          className="w-full px-5 py-2.5 rounded-lg bg-ctp-blue text-ctp-base text-sm font-semibold hover:bg-ctp-sapphire transition-colors"
        >
          {t("requests.uploadMusicFile")}
        </button>
      </div>

      {/* Manual request history */}
      <div>
        <h3 className="text-sm font-semibold text-ctp-subtext0 uppercase tracking-wide mb-3">
          {t("requests.manualRequests")}
        </h3>
        {manualTracks.length === 0 ? (
          <p className="text-ctp-overlay0 text-sm py-6 text-center bg-ctp-mantle rounded-xl border border-ctp-surface0">
            {t("requests.noManualRequests")}
          </p>
        ) : (
          <div className="space-y-2">
            {manualTracks.map((track) => (
              <div
                key={track.id}
                className="bg-ctp-mantle rounded-xl px-4 py-3 border border-ctp-surface0 flex items-center gap-3"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{track.title}</p>
                  {track.artist && (
                    <p className="text-xs text-ctp-subtext0 truncate">{track.artist}</p>
                  )}
                  {track.error_msg && (
                    <p className="text-xs text-ctp-red mt-0.5 truncate">{track.error_msg}</p>
                  )}
                </div>
                <StatusBadge status={track.status} />
              </div>
            ))}
          </div>
        )}
      </div>

      <UploadModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        onUpload={handleUpload}
      />
    </div>
  );
}