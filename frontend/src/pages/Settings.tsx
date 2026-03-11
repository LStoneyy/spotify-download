import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  getSettings,
  updateSettings,
  importCsv,
  getPlaylists,
  addPlaylist,
  deletePlaylist,
  syncPlaylist,
  getAuthStatus,
  login,
  logout,
  type Settings,
  type ImportResult,
  type MonitoredPlaylist,
  type AuthStatus,
} from "../api";
import { supportedLanguages } from "../i18n";

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
  const { t, i18n } = useTranslation();
  const [form, setForm] = useState<Partial<Settings>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");
  const [csvImporting, setCsvImporting] = useState(false);
  const [csvResult, setCsvResult] = useState<ImportResult | null>(null);
  const [csvError, setCsvError] = useState("");
  const csvInputRef = useRef<HTMLInputElement>(null);

  const [playlists, setPlaylists] = useState<MonitoredPlaylist[]>([]);
  const [playlistLoading, setPlaylistLoading] = useState(true);
  const [playlistUrl, setPlaylistUrl] = useState("");
  const [playlistAdding, setPlaylistAdding] = useState(false);
  const [playlistError, setPlaylistError] = useState("");
  const [playlistSuccess, setPlaylistSuccess] = useState("");
  const [syncingId, setSyncingId] = useState<number | null>(null);
  const [authStatus, setAuthStatus] = useState<AuthStatus>({ authenticated: false, expires_at: null });

  useEffect(() => {
    getSettings()
      .then((s) => setForm(s))
      .catch(() => setError(t("errors.failedToLoad")))
      .finally(() => setLoading(false));
  }, [t]);

  useEffect(() => {
    getAuthStatus()
      .then(setAuthStatus)
      .catch(() => setAuthStatus({ authenticated: false, expires_at: null }));
  }, []);

  useEffect(() => {
    setPlaylistLoading(true);
    getPlaylists()
      .then(setPlaylists)
      .catch(() => {})
      .finally(() => setPlaylistLoading(false));
  }, []);

  const handleAddPlaylist = async () => {
    if (!playlistUrl.trim()) return;
    setPlaylistAdding(true);
    setPlaylistError("");
    setPlaylistSuccess("");
    try {
      const added = await addPlaylist(playlistUrl.trim());
      setPlaylists((prev) => [added, ...prev]);
      setPlaylistUrl("");
      setPlaylistSuccess(`${t("success.added")} "${added.name || t("settings.monitoredPlaylists")}"`);
      setTimeout(() => setPlaylistSuccess(""), 3000);
    } catch (err: unknown) {
      setPlaylistError(err instanceof Error ? err.message : t("errors.playlistFailed"));
    } finally {
      setPlaylistAdding(false);
    }
  };

  const handleDeletePlaylist = async (id: number) => {
    try {
      await deletePlaylist(id);
      setPlaylists((prev) => prev.filter((p) => p.id !== id));
    } catch {
      setPlaylistError(t("errors.deleteFailed"));
    }
  };

  const handleSyncPlaylist = async (id: number) => {
    setSyncingId(id);
    setPlaylistError("");
    try {
      const result = await syncPlaylist(id);
      if (result.error) {
        setPlaylistError(result.error);
      } else {
        setPlaylists((prev) =>
          prev.map((p) => (p.id === id ? { ...p, last_synced_at: new Date().toISOString() } : p))
        );
        setPlaylistSuccess(`${t("settings.sync")}: ${result.new_tracks} ${t("settings.tracks")}`);
        setTimeout(() => setPlaylistSuccess(""), 3000);
      }
    } catch (err: unknown) {
      setPlaylistError(err instanceof Error ? err.message : t("errors.syncFailed"));
    } finally {
      setSyncingId(null);
    }
  };

  const handleCsvImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setCsvImporting(true);
    setCsvResult(null);
    setCsvError("");
    try {
      const result = await importCsv(file);
      setCsvResult(result);
    } catch (err: unknown) {
      setCsvError(err instanceof Error ? err.message : t("errors.importFailed"));
    } finally {
      setCsvImporting(false);
      // Reset input so the same file can be re-imported if needed
      if (csvInputRef.current) csvInputRef.current.value = "";
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
      setError(err instanceof Error ? err.message : t("errors.saveFailed"));
    } finally {
      setSaving(false);
    }
  };

  const handleLanguageChange = (lang: string) => {
    i18n.changeLanguage(lang);
    localStorage.setItem('sonus-language', lang);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-40 text-ctp-subtext0">{t("common.loading")}</div>
    );
  }

  const sleepSec = form.sleep_between_downloads ?? 7;

  return (
    <div className="max-w-xl mx-auto space-y-6">
      <h2 className="text-xl font-bold text-ctp-text">{t("settings.title")}</h2>

      {/* Language Selection */}
      <section className="bg-ctp-mantle rounded-xl p-5 border border-ctp-surface0 space-y-4">
        <h3 className="text-sm font-semibold text-ctp-lavender uppercase tracking-wide">{t("settings.language")}</h3>
        <p className="text-xs text-ctp-subtext0">
          {t("settings.languageDescription")}
        </p>
        <div className="flex gap-2">
          {supportedLanguages.map((lang) => (
            <button
              key={lang.code}
              onClick={() => handleLanguageChange(lang.code)}
              className={`px-4 py-2 rounded-lg text-sm font-medium border transition-colors ${
                i18n.language === lang.code || (i18n.language === 'en' && lang.code === 'en')
                  ? "bg-ctp-lavender/20 text-ctp-lavender border-ctp-lavender/40"
                  : "bg-ctp-surface0 text-ctp-subtext0 border-ctp-surface1 hover:border-ctp-overlay0"
              }`}
            >
              {lang.nativeName}
            </button>
          ))}
        </div>
      </section>

      {/* Downloads */}
      <section className="bg-ctp-mantle rounded-xl p-5 border border-ctp-surface0 space-y-4">
        <h3 className="text-sm font-semibold text-ctp-peach uppercase tracking-wide">{t("settings.downloads")}</h3>

        {/* Quality */}
        <div className="space-y-1">
          <label className="text-xs font-medium text-ctp-subtext0">{t("settings.mp3Quality")}</label>
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
            {t("settings.sleepBetweenDownloads")}:{" "}
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
            {t("settings.sleepDescription")}
          </p>
        </div>

        {/* Retries */}
        <div className="space-y-1">
          <label className="text-xs font-medium text-ctp-subtext0">{t("settings.maxRetries")}</label>
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
        <h3 className="text-sm font-semibold text-ctp-mauve uppercase tracking-wide">{t("settings.fileNaming")}</h3>

        <div className="space-y-1">
          <label className="text-xs font-medium text-ctp-subtext0">{t("settings.template")}</label>
          <input
            type="text"
            value={form.file_template ?? "{artist} - {title}"}
            onChange={(e) => set("file_template", e.target.value)}
            className="w-full bg-ctp-surface0 border border-ctp-surface1 rounded-lg px-3 py-2 text-sm text-ctp-text placeholder-ctp-overlay0 font-mono focus:outline-none focus:border-ctp-blue transition-colors"
          />
          <p className="text-xs text-ctp-overlay0">
            {t("settings.templateVariables")}
          </p>
        </div>

        {/* Live preview */}
        <div className="bg-ctp-surface0 rounded-lg px-4 py-3">
          <p className="text-xs text-ctp-subtext0 mb-1 font-medium">{t("settings.preview")}</p>
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

      {/* Spotify Authentication */}
      <section className="bg-ctp-mantle rounded-xl p-5 border border-ctp-surface0 space-y-4">
        <h3 className="text-sm font-semibold text-ctp-green uppercase tracking-wide">{t("settings.spotifyAuth")}</h3>
        <p className="text-xs text-ctp-subtext0">
          {t("settings.spotifyAuthDescription")}
        </p>
        
        {authStatus.authenticated ? (
          <div className="flex items-center justify-between bg-ctp-surface0 rounded-lg px-4 py-3">
            <div>
              <p className="text-sm text-ctp-text font-medium">✓ {t("settings.authenticated")}</p>
              {authStatus.expires_at && (
                <p className="text-xs text-ctp-subtext0">
                  {t("settings.tokenExpires")}: {new Date(authStatus.expires_at * 1000).toLocaleString()}
                </p>
              )}
            </div>
            <button
              onClick={() => logout().then(() => setAuthStatus({ authenticated: false, expires_at: null }))}
              className="px-3 py-1 text-xs rounded-lg bg-ctp-red/20 text-ctp-red border border-ctp-red/30 hover:bg-ctp-red/30 transition-colors"
            >
              {t("settings.logout")}
            </button>
          </div>
        ) : (
          <button
            onClick={login}
            className="w-full py-2.5 rounded-lg bg-ctp-green/20 text-ctp-green border border-ctp-green/30 text-sm font-bold hover:bg-ctp-green/30 transition-colors"
          >
            {t("settings.loginWithSpotify")}
          </button>
        )}
      </section>

      {/* Monitored Playlists */}
      <section className="bg-ctp-mantle rounded-xl p-5 border border-ctp-surface0 space-y-4">
        <h3 className="text-sm font-semibold text-ctp-teal uppercase tracking-wide">{t("settings.monitoredPlaylists")}</h3>
        <p className="text-xs text-ctp-subtext0">
          {t("settings.monitoredPlaylistsDescription")}
        </p>

        {!authStatus.authenticated && (
          <div className="px-4 py-3 rounded-xl bg-ctp-yellow/10 border border-ctp-yellow/30 text-ctp-yellow text-sm">
            {t("settings.pleaseAuthenticate")}
          </div>
        )}

        {playlistError && (
          <div className="px-4 py-3 rounded-xl bg-ctp-red/10 border border-ctp-red/30 text-ctp-red text-sm">
            {playlistError}
          </div>
        )}
        {playlistSuccess && (
          <div className="px-4 py-3 rounded-xl bg-ctp-green/10 border border-ctp-green/30 text-ctp-green text-sm">
            ✓ {playlistSuccess}
          </div>
        )}

        <div className="flex gap-2">
          <input
            type="text"
            value={playlistUrl}
            onChange={(e) => setPlaylistUrl(e.target.value)}
            placeholder={t("settings.playlistPlaceholder")}
            className="flex-1 bg-ctp-surface0 border border-ctp-surface1 rounded-lg px-3 py-2 text-sm text-ctp-text placeholder-ctp-overlay0 focus:outline-none focus:border-ctp-teal transition-colors"
            onKeyDown={(e) => e.key === "Enter" && handleAddPlaylist()}
          />
          <button
            onClick={handleAddPlaylist}
            disabled={playlistAdding || !playlistUrl.trim() || !authStatus.authenticated}
            className="px-4 py-2 rounded-lg bg-ctp-teal/20 text-ctp-teal border border-ctp-teal/30 text-sm font-bold hover:bg-ctp-teal/30 disabled:opacity-50 transition-colors"
          >
            {playlistAdding ? `${t("settings.adding")}…` : t("settings.add")}
          </button>
        </div>

        {playlistLoading ? (
          <p className="text-xs text-ctp-subtext0">{t("common.loading")}</p>
        ) : playlists.length === 0 ? (
          <p className="text-xs text-ctp-overlay0">{t("settings.noPlaylists")}</p>
        ) : (
          <div className="space-y-2">
            {playlists.map((p) => (
              <div
                key={p.id}
                className="flex items-center justify-between bg-ctp-surface0 rounded-lg px-4 py-3"
              >
                <div className="min-w-0 flex-1">
                  <p className="text-sm text-ctp-text font-medium truncate">
                    {p.name || t("settings.monitoredPlaylists")}
                  </p>
                  <p className="text-xs text-ctp-subtext0">
                    {p.track_count} {t("settings.tracks")}
                    {p.last_synced_at && (
                      <span>
                        {" "}
                        · {t("settings.lastSynced")}{" "}
                        {new Date(p.last_synced_at).toLocaleDateString(undefined, {
                          month: "short",
                          day: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </span>
                    )}
                  </p>
                  {p.sync_error && (
                    <p className="text-xs text-ctp-red truncate">{t("errors.syncFailed")}: {p.sync_error}</p>
                  )}
                </div>
                <div className="flex gap-2 ml-2">
                  <button
                    onClick={() => handleSyncPlaylist(p.id)}
                    disabled={syncingId === p.id}
                    className="px-3 py-1 text-xs rounded-lg bg-ctp-blue/20 text-ctp-blue border border-ctp-blue/30 hover:bg-ctp-blue/30 disabled:opacity-50 transition-colors"
                  >
                    {syncingId === p.id ? `${t("settings.syncing")}…` : t("settings.sync")}
                  </button>
                  <button
                    onClick={() => handleDeletePlaylist(p.id)}
                    className="px-3 py-1 text-xs rounded-lg bg-ctp-red/20 text-ctp-red border border-ctp-red/30 hover:bg-ctp-red/30 transition-colors"
                  >
                    {t("settings.remove")}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* CSV Import */}
      <section className="bg-ctp-mantle rounded-xl p-5 border border-ctp-surface0 space-y-4">
        <h3 className="text-sm font-semibold text-ctp-yellow uppercase tracking-wide">{t("settings.csvImport")}</h3>
        <p className="text-xs text-ctp-subtext0">
          {t("settings.csvImportDescription")}
        </p>
        <p className="text-xs text-ctp-subtext0">
          {t("settings.csvImportDescription2")}
        </p>

        {csvResult && (
          <div className="flex items-start gap-2 px-4 py-3 rounded-xl bg-ctp-green/10 border border-ctp-green/30 text-ctp-green text-sm">
            <span>✓</span>
            <span>
              {t("settings.imported")} <strong>{csvResult.imported}</strong> {t("settings.importedDescription")}
              {csvResult.skipped > 0 && ` (${csvResult.skipped} ${t("settings.alreadyExisted")})`}.
              {t("settings.seeDashboard")}
            </span>
          </div>
        )}
        {csvError && (
          <div className="px-4 py-3 rounded-xl bg-ctp-red/10 border border-ctp-red/30 text-ctp-red text-sm">
            {csvError}
          </div>
        )}

        <input
          ref={csvInputRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={handleCsvImport}
        />
        <button
          onClick={() => csvInputRef.current?.click()}
          disabled={csvImporting}
          className="w-full py-2.5 rounded-lg bg-ctp-yellow/20 text-ctp-yellow border border-ctp-yellow/30 text-sm font-bold hover:bg-ctp-yellow/30 disabled:opacity-50 transition-colors"
        >
          {csvImporting ? `${t("settings.importing")}…` : t("settings.chooseFile")}
        </button>
      </section>

      {/* Cookies hint */}
      <section className="bg-ctp-surface0/50 rounded-xl p-4 border border-ctp-surface0 text-xs text-ctp-subtext0 space-y-1">
        <p className="font-semibold text-ctp-text">{t("settings.youtubeCookies")}</p>
        <p>
          {t("settings.youtubeCookiesDescription")}
        </p>
        <p>{t("settings.addToCompose")}</p>
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
        {saving ? `${t("settings.saving")}…` : saved ? t("settings.saved") : t("settings.save")}
      </button>
    </div>
  );
}