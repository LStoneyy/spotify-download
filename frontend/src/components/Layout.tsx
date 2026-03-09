import { NavLink, Outlet } from "react-router-dom";

const navItems = [
  { to: "/", label: "Dashboard", icon: "📊" },
  { to: "/requests", label: "Requests", icon: "🎵" },
  { to: "/settings", label: "Settings", icon: "⚙️" },
];

function Logo({ className = "" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="12" cy="12" r="11" fill="#1a1a2e"/>
      <path d="M12 4V14M12 14L8 10M12 14L16 10" stroke="#1DB954" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M7 17C9 16 11 16 13 17C15 18 17 18 19 17" stroke="#1DB954" strokeWidth="2" strokeLinecap="round" opacity="0.9"/>
      <path d="M5 20C8 18 11 18 13 20C15 22 18 21 21 19" stroke="#1DB954" strokeWidth="2" strokeLinecap="round" opacity="0.6"/>
    </svg>
  );
}

export default function Layout() {
  return (
    <div className="flex flex-col lg:flex-row min-h-screen bg-ctp-base text-ctp-text">
      {/* ── Desktop sidebar ───────────────────────────────────────────── */}
      <aside className="hidden lg:flex flex-col w-56 min-h-screen bg-ctp-mantle border-r border-ctp-surface0 flex-shrink-0">
        <div className="px-6 py-5 border-b border-ctp-surface0 flex items-center gap-3">
          <Logo className="w-8 h-8" />
          <div>
            <h1 className="text-ctp-text font-bold text-base leading-tight">Spotify Downloader</h1>
          </div>
        </div>
        <nav className="flex flex-col gap-1 p-3 flex-1">
          {navItems.map(({ to, label, icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-ctp-surface0 text-ctp-blue"
                    : "text-ctp-subtext0 hover:bg-ctp-surface0/50 hover:text-ctp-text"
                }`
              }
            >
              <span className="text-base">{icon}</span>
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="p-4 text-xs text-ctp-overlay0 border-t border-ctp-surface0">
          spotify-download v2
        </div>
      </aside>

      {/* ── Main content ──────────────────────────────────────────────── */}
      <div className="flex flex-col flex-1 min-w-0 pb-16 lg:pb-0">
        {/* Mobile top header */}
        <header className="lg:hidden flex items-center gap-3 px-4 py-3 bg-ctp-mantle border-b border-ctp-surface0 sticky top-0 z-10">
          <Logo className="w-6 h-6" />
          <h1 className="text-ctp-text font-bold text-base">Spotify Downloader</h1>
        </header>

        <main className="flex-1 p-4 md:p-6 overflow-auto">
          <Outlet />
        </main>
      </div>

      {/* ── Mobile bottom tab bar ─────────────────────────────────────── */}
      <nav className="lg:hidden fixed bottom-0 inset-x-0 z-20 flex bg-ctp-mantle border-t border-ctp-surface0">
        {navItems.map(({ to, label, icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              `flex-1 flex flex-col items-center justify-center py-2 text-xs font-medium transition-colors ${
                isActive ? "text-ctp-blue" : "text-ctp-subtext0 hover:text-ctp-text"
              }`
            }
          >
            <span className="text-lg mb-0.5">{icon}</span>
            {label}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
