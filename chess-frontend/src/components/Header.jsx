export default function Header() {
  return (
    <aside className="w-full h-full flex flex-col py-4">
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 mb-8">
        <div
          className="w-8 h-8 rounded flex items-center justify-center"
          style={{ background: 'var(--accent-green)' }}
        >
          <span className="text-white text-base font-bold" style={{ lineHeight: 1 }}>♞</span>
        </div>
        <span
          className="text-xl font-bold tracking-tight"
          style={{ color: 'var(--text-bright)' }}
        >
          Chess.com
        </span>
      </div>

      {/* Nav */}
      <nav className="flex flex-col gap-1 px-2">
        {['Play', 'Puzzles', 'Learn', 'Watch', 'News', 'Social'].map((item, i) => (
          <button
            key={item}
            className="flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-semibold transition-colors text-left"
            style={{
              color: i === 0 ? 'var(--text-bright)' : 'var(--text-secondary)',
              background: i === 0 ? 'var(--bg-sidebar-alt)' : 'transparent',
              border: 'none',
              cursor: 'pointer',
            }}
          >
            <span className="opacity-70 text-lg">
              {i === 0 ? '♟' : i === 1 ? '🧩' : i === 2 ? '🎓' : i === 3 ? '📺' : i === 4 ? '📰' : '👥'}
            </span>
            {item}
          </button>
        ))}
      </nav>

      <div className="mt-auto px-4 pb-4 flex flex-col gap-3">
        <button className="btn btn-primary w-full py-3" style={{ background: 'var(--accent-green)', borderRadius: 'var(--radius-sm)' }}>
          Sign Up
        </button>
        <button className="btn btn-secondary w-full py-3" style={{ background: 'var(--bg-card)', border: 'none', borderRadius: 'var(--radius-sm)' }}>
          Log In
        </button>
      </div>
    </aside>
  )
}
