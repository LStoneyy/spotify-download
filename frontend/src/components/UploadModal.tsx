import { useState, useRef } from "react";
import { useTranslation } from "react-i18next";

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUpload: (file: File, title: string, artist: string, album: string) => Promise<void>;
}

const ACCEPTED_AUDIO_TYPES = [
  "audio/mpeg",
  "audio/mp3",
  "audio/wav",
  "audio/x-wav",
  "audio/flac",
  "audio/x-flac",
  "audio/mp4",
  "audio/m4a",
  "audio/x-m4a",
  "audio/ogg",
  "audio/x-ogg",
  "audio/wma",
  "audio/x-ms-wma",
  "audio/aac",
  "audio/x-aac",
  "audio/opus",
  "audio/webm",
];

export default function UploadModal({ isOpen, onClose, onUpload }: UploadModalProps) {
  const { t } = useTranslation();
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [artist, setArtist] = useState("");
  const [album, setAlbum] = useState("");
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    if (!ACCEPTED_AUDIO_TYPES.includes(selectedFile.type) && !selectedFile.name.match(/\.(mp3|wav|flac|m4a|ogg|wma|aac|opus|webm)$/i)) {
      setError(t("upload.uploadError"));
      return;
    }

    setFile(selectedFile);
    setError("");
    const fileName = selectedFile.name.replace(/\.[^/.]+$/, "");
    setTitle(fileName);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !title.trim() || !artist.trim()) {
      setError(t("upload.uploadError"));
      return;
    }

    setUploading(true);
    setError("");

    try {
      await onUpload(file, title.trim(), artist.trim(), album.trim());
      handleClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : t("upload.uploadError"));
    } finally {
      setUploading(false);
    }
  };

  const handleClose = () => {
    setFile(null);
    setTitle("");
    setArtist("");
    setAlbum("");
    setError("");
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-ctp-mantle rounded-xl border border-ctp-surface0 w-full max-w-md shadow-xl">
        <div className="flex items-center justify-between px-5 py-4 border-b border-ctp-surface0">
          <h3 className="text-lg font-bold text-ctp-text">{t("upload.title")}</h3>
          <button
            onClick={handleClose}
            className="text-ctp-subtext0 hover:text-ctp-text text-xl leading-none"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div>
            <label className="block text-sm font-medium text-ctp-text mb-2">
              {t("upload.selectFile")}
            </label>
            <input
              ref={fileInputRef}
              type="file"
              accept="audio/*,.mp3,.wav,.flac,.m4a,.ogg,.wma,.aac,.opus,.webm"
              onChange={handleFileSelect}
              className="w-full text-sm text-ctp-text file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-ctp-surface0 file:text-ctp-text hover:file:bg-ctp-surface1 cursor-pointer"
            />
            {file && (
              <p className="mt-2 text-xs text-ctp-subtext0">
                {file.name}
              </p>
            )}
            <p className="mt-1 text-xs text-ctp-overlay0">
              {t("upload.supportedFormats")}
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-ctp-text mb-2">
              {t("upload.titleLabel")} <span className="text-ctp-red">*</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder={t("upload.titlePlaceholder")}
              className="w-full bg-ctp-surface0 border border-ctp-surface1 rounded-lg px-4 py-2.5 text-sm text-ctp-text placeholder-ctp-overlay0 focus:outline-none focus:border-ctp-blue transition-colors"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-ctp-text mb-2">
              {t("upload.artistLabel")} <span className="text-ctp-red">*</span>
            </label>
            <input
              type="text"
              value={artist}
              onChange={(e) => setArtist(e.target.value)}
              placeholder={t("upload.artistPlaceholder")}
              className="w-full bg-ctp-surface0 border border-ctp-surface1 rounded-lg px-4 py-2.5 text-sm text-ctp-text placeholder-ctp-overlay0 focus:outline-none focus:border-ctp-blue transition-colors"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-ctp-text mb-2">
              {t("upload.albumLabel")}
            </label>
            <input
              type="text"
              value={album}
              onChange={(e) => setAlbum(e.target.value)}
              placeholder={t("upload.albumPlaceholder")}
              className="w-full bg-ctp-surface0 border border-ctp-surface1 rounded-lg px-4 py-2.5 text-sm text-ctp-text placeholder-ctp-overlay0 focus:outline-none focus:border-ctp-blue transition-colors"
            />
          </div>

          {error && (
            <p className="text-sm text-ctp-red bg-ctp-red/10 px-3 py-2 rounded-lg">
              {error}
            </p>
          )}

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={handleClose}
              className="flex-1 px-4 py-2.5 rounded-lg bg-ctp-surface0 text-ctp-text text-sm font-medium hover:bg-ctp-surface1 transition-colors"
            >
              {t("upload.cancel")}
            </button>
            <button
              type="submit"
              disabled={uploading || !file || !title.trim() || !artist.trim()}
              className="flex-1 px-4 py-2.5 rounded-lg bg-ctp-green text-ctp-base text-sm font-semibold hover:bg-ctp-teal disabled:opacity-50 transition-colors"
            >
              {uploading ? t("upload.uploading") : t("upload.upload")}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}