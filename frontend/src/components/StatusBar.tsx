import { type StatusResponse } from "../api";

interface Props {
  status: StatusResponse | null;
}

export default function StatusBar({ status }: Props) {
  if (!status?.currently_downloading) return null;
  const { title, artist } = status.currently_downloading;

  return (
    <div className="flex items-center gap-3 bg-ctp-surface0 border border-ctp-teal/30 rounded-xl px-4 py-3 mb-4">
      <span className="animate-pulse-green w-2.5 h-2.5 rounded-full bg-ctp-green flex-shrink-0" />
      <div className="min-w-0">
        <p className="text-xs text-ctp-subtext0 font-medium uppercase tracking-wide">
          Downloading now
        </p>
        <p className="text-sm text-ctp-text font-semibold truncate">
          {artist ? `${artist} – ${title}` : title}
        </p>
      </div>
    </div>
  );
}
