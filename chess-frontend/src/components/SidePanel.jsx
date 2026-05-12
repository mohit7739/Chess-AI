import { useEffect, useRef } from 'react'

export default function SidePanel({
  moves,
  activeMoveIndex,
  status,
  gameResult,
  inCheck,
  turn,
  onNewGame,
  goFirst,
  goPrev,
  goNext,
  goLast,
  goToMove,
}) {
  const scrollRef = useRef(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [moves])

  const pairs = []
  for (let i = 0; i < moves.length; i += 2) {
    pairs.push({
      number: Math.floor(i / 2) + 1,
      white: moves[i] || null,
      black: moves[i + 1] || null,
      whiteIdx: i,
      blackIdx: i + 1,
    })
  }

  return (
    <div
      className="flex flex-col w-full lg:w-[320px]"
      style={{
        background: 'var(--bg-sidebar)',
        borderRadius: '0 var(--radius-lg) var(--radius-lg) 0',
        borderLeft: '1px solid var(--border-default)',
      }}
    >
      {/* ── Top bar ─────────────────────────────────── */}
      <div
        className="flex items-center justify-between px-4 py-3"
        style={{ borderBottom: '1px solid var(--border-default)' }}
      >
        <span className="text-xs font-semibold" style={{ color: 'var(--text-secondary)' }}>
          vs Computer
        </span>
        <div className="flex items-center gap-1.5">
          {status === 'ai-thinking' && (
            <span
              className="text-[10px] px-2 py-0.5 rounded-md font-medium"
              style={{ background: 'rgba(90, 159, 212, 0.1)', color: 'var(--accent-blue)' }}
            >
              Thinking…
            </span>
          )}
          {inCheck && status !== 'game-over' && (
            <span
              className="text-[10px] px-2 py-0.5 rounded-md font-semibold"
              style={{ background: 'rgba(217, 85, 85, 0.1)', color: 'var(--accent-red)' }}
            >
              Check
            </span>
          )}
        </div>
      </div>

      {/* ── Move history ──────────────────────────────── */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-1.5 py-1.5" style={{ minHeight: '200px' }}>
        {pairs.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full py-14 gap-2.5">
            <span className="text-3xl opacity-15">♟</span>
            <p className="text-[11px]" style={{ color: 'var(--text-muted)' }}>
              Make your first move
            </p>
          </div>
        ) : (
          <div>
            {pairs.map((pair) => (
              <div key={pair.number} className="flex items-center move-row" style={{ minHeight: '30px' }}>
                <span
                  className="w-8 text-right pr-2 text-[11px] font-medium shrink-0"
                  style={{ color: 'var(--text-muted)' }}
                >
                  {pair.number}.
                </span>
                <span
                  className={`flex-1 text-[12px] font-mono font-medium move-cell ${pair.whiteIdx === activeMoveIndex ? 'active' : ''}`}
                  style={pair.whiteIdx !== activeMoveIndex ? { color: 'var(--text-primary)' } : {}}
                  onClick={() => goToMove(pair.whiteIdx)}
                >
                  {pair.white?.san || ''}
                </span>
                <span
                  className={`flex-1 text-[12px] font-mono font-medium move-cell ${pair.blackIdx === activeMoveIndex ? 'active' : ''}`}
                  style={pair.blackIdx !== activeMoveIndex ? { color: 'var(--text-primary)' } : {}}
                  onClick={() => pair.black && goToMove(pair.blackIdx)}
                >
                  {pair.black?.san || ''}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── Game result ────────────────────────────────── */}
      {gameResult && (
        <div
          className="mx-3 mb-2.5 py-3 px-4 rounded-lg text-center text-sm font-bold animate-fade-in"
          style={{
            background: gameResult.startsWith('1-0')
              ? 'rgba(127, 186, 60, 0.1)'
              : gameResult.startsWith('0-1')
                ? 'rgba(217, 85, 85, 0.1)'
                : 'rgba(255, 255, 255, 0.04)',
            color: gameResult.startsWith('1-0')
              ? 'var(--accent-green)'
              : gameResult.startsWith('0-1')
                ? 'var(--accent-red)'
                : 'var(--text-secondary)',
            border: '1px solid var(--border-default)',
          }}
        >
          {gameResult}
        </div>
      )}

      {/* ── Move Navigation Bar ────────────────────────── */}
      <div className="flex items-center justify-between px-3 py-2" style={{ borderTop: '1px solid var(--border-strong)', background: 'var(--bg-sidebar-alt)' }}>
        <button className="btn btn-secondary flex-1" style={{ padding: '6px', border: 'none', background: 'transparent' }} onClick={goFirst} title="First Move">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="19 20 9 12 19 4 19 20"></polygon><line x1="5" y1="19" x2="5" y2="5"></line></svg>
        </button>
        <button className="btn btn-secondary flex-1" style={{ padding: '6px', border: 'none', background: 'transparent' }} onClick={goPrev} title="Previous Move">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="15 18 9 12 15 6 15 18"></polygon></svg>
        </button>
        <button className="btn btn-secondary flex-1" style={{ padding: '6px', border: 'none', background: 'transparent' }} onClick={goNext} title="Next Move">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="9 18 15 12 9 6 9 18"></polygon></svg>
        </button>
        <button className="btn btn-secondary flex-1" style={{ padding: '6px', border: 'none', background: 'transparent' }} onClick={goLast} title="Last Move">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="5 4 15 12 5 20 5 4"></polygon><line x1="19" y1="5" x2="19" y2="19"></line></svg>
        </button>
      </div>

      {/* ── Controls ───────────────────────────────────── */}
      <div
        className="px-3 py-3 flex items-center gap-2"
        style={{ borderTop: '1px solid var(--border-default)' }}
      >
        <button
          id="new-game-button"
          className="btn btn-primary flex-1"
          onClick={onNewGame}
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="23 4 23 10 17 10" />
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
          </svg>
          New Game
        </button>

        <button
          className="btn btn-secondary"
          title="Flip board"
          style={{ padding: '9px 11px' }}
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="17 1 21 5 17 9" />
            <path d="M3 11V9a4 4 0 0 1 4-4h14" />
            <polyline points="7 23 3 19 7 15" />
            <path d="M21 13v2a4 4 0 0 1-4 4H3" />
          </svg>
        </button>

        <button
          className="btn btn-danger"
          title="Resign"
          style={{ padding: '9px 11px' }}
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z" />
            <line x1="4" y1="22" x2="4" y2="15" />
          </svg>
        </button>
      </div>
    </div>
  )
}
