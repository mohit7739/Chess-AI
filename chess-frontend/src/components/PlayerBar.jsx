const PIECE_UNICODE = {
  w: { p: '♙', n: '♘', b: '♗', r: '♖', q: '♕' },
  b: { p: '♟', n: '♞', b: '♝', r: '♜', q: '♛' },
}
const PIECE_ORDER = ['p', 'n', 'b', 'r', 'q']

export default function PlayerBar({
  name,
  subtitle,
  color,
  isActive,
  captured = [],
  materialDiff = 0,
  isBottom = false,
  isThinking = false,
}) {
  const sortedCaptured = [...captured].sort(
    (a, b) => PIECE_ORDER.indexOf(a) - PIECE_ORDER.indexOf(b)
  )
  const capturedColor = color === 'w' ? 'b' : 'w'

  return (
    <div
      className="flex items-center justify-between px-3.5 py-2.5"
      style={{
        background: isActive ? 'var(--bg-player-bar-active)' : 'var(--bg-player-bar)',
        borderRadius: isBottom
          ? '0 0 var(--radius-lg) var(--radius-lg)'
          : 'var(--radius-lg) var(--radius-lg) 0 0',
        borderLeft: isActive ? '3px solid var(--accent-green)' : '3px solid transparent',
        transition: 'all 0.25s ease',
        minHeight: '44px',
      }}
    >
      {/* Left: avatar + name */}
      <div className="flex items-center gap-2.5">
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold"
          style={{
            background: color === 'w' ? '#e0ded8' : '#3a3a3a',
            color: color === 'w' ? '#1a1a1a' : '#d4d4d4',
          }}
        >
          {color === 'w' ? '♔' : '♚'}
        </div>

        <div className="flex flex-col">
          <div className="flex items-center gap-2">
            <span className="text-[13px] font-semibold" style={{ color: 'var(--text-primary)' }}>
              {name}
            </span>
            {isThinking && (
              <span className="flex items-center gap-0.5 ml-0.5">
                {[0, 1, 2].map((i) => (
                  <span
                    key={i}
                    className="w-1 h-1 rounded-full"
                    style={{
                      background: 'var(--accent-green)',
                      animation: `thinking-dots 1.4s ease-in-out ${i * 0.16}s infinite`,
                    }}
                  />
                ))}
              </span>
            )}
          </div>
          <span className="text-[10px] font-medium" style={{ color: 'var(--text-muted)' }}>
            {subtitle}
          </span>
        </div>
      </div>

      {/* Right: captured pieces + material advantage */}
      <div className="flex items-center gap-2">
        {sortedCaptured.length > 0 && (
          <div className="flex items-center">
            {sortedCaptured.map((piece, i) => (
              <span
                key={`${piece}-${i}`}
                className="captured-piece"
                style={{ color: capturedColor === 'w' ? '#b8b5b0' : '#555' }}
              >
                {PIECE_UNICODE[capturedColor][piece]}
              </span>
            ))}
          </div>
        )}
        {materialDiff > 0 && (
          <span
            className="text-[11px] font-bold"
            style={{ color: 'var(--text-secondary)' }}
          >
            +{materialDiff}
          </span>
        )}
      </div>
    </div>
  )
}
