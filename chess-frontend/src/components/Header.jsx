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
        <div className="flex items-center gap-2">
          <div
            className="w-7 h-7 rounded-lg flex items-center justify-center"
            style={{ background: 'var(--accent-green)' }}
          >
            <span className="text-white text-sm font-bold" style={{ lineHeight: 1 }}>♞</span>
          </div>
          <span
            className="text-sm font-bold tracking-tight"
            style={{ color: 'var(--text-bright)' }}
          >
            ChessAI
          </span>
        </div>

        {/* Nav */}
        <nav className="hidden md:flex items-center gap-0.5 ml-3">
          {['Play', 'Analysis', 'Learn'].map((item, i) => (
            <button
              key={item}
              className="px-3 py-1.5 rounded-md text-xs font-medium transition-colors"
              style={{
                color: i === 0 ? 'var(--text-bright)' : 'var(--text-muted)',
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

      {/* Right side — Online status */}
      <div className="flex items-center gap-3">
        <div
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium"
          style={{
            background: 'rgba(127, 186, 60, 0.1)',
            color: 'var(--accent-green)',
          }}
        >
          <span
            className="w-1.5 h-1.5 rounded-full"
            style={{
              background: 'var(--accent-green)',
              animation: 'pulse-dot 2s ease-in-out infinite',
            }}
          />
          Online
        </div>
      </div>
    </header>
  )
}
