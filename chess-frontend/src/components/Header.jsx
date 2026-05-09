export default function Header() {
  return (
    <header
      className="w-full flex items-center justify-between px-5 py-2.5"
      style={{
        background: 'var(--bg-sidebar)',
        borderBottom: '1px solid var(--border-default)',
      }}
    >
      <div className="flex items-center gap-2.5">
        {/* Logo */}
        <div className="flex items-center gap-1.5">
          <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
            <rect width="28" height="28" rx="6" fill="var(--accent-green)" />
            <text x="14" y="20" textAnchor="middle" fill="white" fontSize="16" fontWeight="700" fontFamily="Inter">♞</text>
          </svg>
          <span
            className="text-base font-bold tracking-tight"
            style={{ color: 'var(--text-bright)' }}
          >
            chess
          </span>
        </div>

        {/* Nav */}
        <nav className="hidden md:flex items-center gap-1 ml-4">
          {['Play', 'Puzzles', 'Learn'].map((item, i) => (
            <button
              key={item}
              className="px-3 py-1.5 rounded text-xs font-semibold transition-colors"
              style={{
                color: i === 0 ? 'var(--text-bright)' : 'var(--text-secondary)',
                background: i === 0 ? 'var(--bg-sidebar-alt)' : 'transparent',
                border: 'none',
                cursor: 'pointer',
              }}
            >
              {item}
            </button>
          ))}
        </nav>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-3">
        <div
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium"
          style={{
            background: 'rgba(129, 182, 76, 0.12)',
            color: 'var(--accent-green)',
          }}
        >
          <span
            className="w-1.5 h-1.5 rounded-full"
            style={{ background: 'var(--accent-green)', animation: 'pulse-dot 2s ease-in-out infinite' }}
          />
          Online
        </div>
      </div>
    </header>
  )
}
