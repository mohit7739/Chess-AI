import { useState, useCallback, useRef, useMemo } from 'react'
import { Chess } from 'chess.js'
import ChessBoard from './components/ChessBoard'
import PlayerBar from './components/PlayerBar'
import SidePanel from './components/SidePanel'
import Header from './components/Header'

// Use Vercel environment variable for production, or fallback to local backend
const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/get-move'

// Piece values for material calculation
const PIECE_VALUES = { p: 1, n: 3, b: 3, r: 5, q: 9 }
const INITIAL_PIECES = { p: 8, n: 2, b: 2, r: 2, q: 1 }

function getCapturedPieces(game) {
  const board = game.board().flat().filter(Boolean)
  const current = { w: { p: 0, n: 0, b: 0, r: 0, q: 0 }, b: { p: 0, n: 0, b: 0, r: 0, q: 0 } }

  board.forEach((sq) => {
    if (sq.type !== 'k') current[sq.color][sq.type]++
  })

  const captured = { w: [], b: [] }
  let materialDiff = 0

  for (const piece of Object.keys(INITIAL_PIECES)) {
    // Pieces captured BY white (black pieces missing)
    const blackMissing = INITIAL_PIECES[piece] - current.b[piece]
    for (let i = 0; i < blackMissing; i++) captured.w.push(piece)
    // Pieces captured BY black (white pieces missing)
    const whiteMissing = INITIAL_PIECES[piece] - current.w[piece]
    for (let i = 0; i < whiteMissing; i++) captured.b.push(piece)

    materialDiff += (current.w[piece] - current.b[piece]) * PIECE_VALUES[piece]
  }

  return { captured, materialDiff }
}

function App() {
  const [game, setGame] = useState(new Chess())
  const [boardPosition, setBoardPosition] = useState(game.fen())
  const [moveHistory, setMoveHistory] = useState([])
  const [fenHistory, setFenHistory] = useState([new Chess().fen()]) // track every position
  const [status, setStatus] = useState('your-turn')
  const [gameResult, setGameResult] = useState(null)
  const [lastMove, setLastMove] = useState(null)
  const [activeMoveIndex, setActiveMoveIndex] = useState(-1)
  const [isViewingHistory, setIsViewingHistory] = useState(false)
  const aiThinking = useRef(false)

  const { captured, materialDiff } = useMemo(() => getCapturedPieces(game), [boardPosition])

  const updateStatus = useCallback((g) => {
    if (g.isGameOver()) {
      setStatus('game-over')
      if (g.isCheckmate()) {
        setGameResult(g.turn() === 'w' ? '0-1 Black wins' : '1-0 White wins')
      } else if (g.isDraw()) {
        setGameResult('½-½ Draw')
      } else if (g.isStalemate()) {
        setGameResult('½-½ Stalemate')
      } else if (g.isThreefoldRepetition()) {
        setGameResult('½-½ Repetition')
      } else if (g.isInsufficientMaterial()) {
        setGameResult('½-½ Insufficient material')
      } else {
        setGameResult('Game over')
      }
    }
  }, [])

  const requestAIMove = useCallback(async (fen) => {
    if (aiThinking.current) return
    aiThinking.current = true
    setStatus('ai-thinking')

    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fen }),
      })
      if (!res.ok) throw new Error(`API error: ${res.status}`)

      const data = await res.json()
      if (data.error || !data.move) {
        console.error('AI returned error:', data.error || 'no move')
        setStatus('your-turn')
        aiThinking.current = false
        return
      }
      const aiMove = data.move

      setGame((prev) => {
        const g = new Chess(prev.fen())
        const from = aiMove.substring(0, 2)
        const to = aiMove.substring(2, 4)
        const promotion = aiMove.length > 4 ? aiMove[4] : undefined

        const result = g.move({ from, to, promotion })
        if (result) {
          setBoardPosition(g.fen())
          setFenHistory((h) => [...h, g.fen()])
          setMoveHistory((h) => {
            const next = [...h, { color: 'b', san: result.san, from, to }]
            setActiveMoveIndex(next.length - 1)
            return next
          })
          setLastMove({ from, to })
          updateStatus(g)
          if (!g.isGameOver()) setStatus('your-turn')
        }
        return g
      })
    } catch (err) {
      console.error('AI move error:', err)
      setStatus('your-turn')
    } finally {
      aiThinking.current = false
    }
  }, [updateStatus])

  const onDrop = useCallback((sourceSquare, targetSquare, piece) => {
    if (status === 'ai-thinking' || status === 'game-over' || isViewingHistory) return false

    const g = new Chess(game.fen())

    let isPromotion = false
    if (piece) {
      const pieceType = typeof piece === 'string' ? piece : piece?.pieceType
      isPromotion = pieceType?.[1] === 'P' && (targetSquare[1] === '8' || targetSquare[1] === '1')
    } else {
      const srcPiece = g.get(sourceSquare)
      isPromotion = srcPiece?.type === 'p' && (targetSquare[1] === '8' || targetSquare[1] === '1')
    }
    const promotion = isPromotion ? 'q' : undefined

    const move = g.move({ from: sourceSquare, to: targetSquare, promotion })
    if (move === null) return false

    setGame(g)
    setBoardPosition(g.fen())
    setFenHistory((h) => [...h, g.fen()])
    setMoveHistory((h) => {
      const next = [...h, { color: 'w', san: move.san, from: sourceSquare, to: targetSquare }]
      setActiveMoveIndex(next.length - 1)
      return next
    })
    setLastMove({ from: sourceSquare, to: targetSquare })
    updateStatus(g)

    if (!g.isGameOver()) {
      requestAIMove(g.fen())
    }

    return true
  }, [game, status, isViewingHistory, requestAIMove, updateStatus])

  const resetGame = useCallback(() => {
    const g = new Chess()
    setGame(g)
    setBoardPosition(g.fen())
    setMoveHistory([])
    setFenHistory([g.fen()])
    setStatus('your-turn')
    setGameResult(null)
    setLastMove(null)
    setActiveMoveIndex(-1)
    setIsViewingHistory(false)
    aiThinking.current = false
  }, [])

  const resignGame = useCallback(() => {
    if (status === 'game-over') return
    setStatus('game-over')
    setGameResult('0-1 (White resigned)')
  }, [status])

  // ── Move Navigation ─────────────────────────────
  const goToMove = useCallback((idx) => {
    // idx = -1 means starting position, 0 = after first move, etc.
    const fenIdx = idx + 1 // fenHistory[0] is starting position
    if (fenIdx >= 0 && fenIdx < fenHistory.length) {
      setBoardPosition(fenHistory[fenIdx])
      setActiveMoveIndex(idx)
      const atLatest = fenIdx === fenHistory.length - 1
      setIsViewingHistory(!atLatest)
      if (idx >= 0) {
        const m = moveHistory[idx]
        if (m) setLastMove({ from: m.from, to: m.to })
      } else {
        setLastMove(null)
      }
    }
  }, [fenHistory, moveHistory])

  const goFirst = useCallback(() => goToMove(-1), [goToMove])
  const goLast = useCallback(() => goToMove(moveHistory.length - 1), [goToMove, moveHistory])
  const goPrev = useCallback(() => goToMove(Math.max(-1, activeMoveIndex - 1)), [goToMove, activeMoveIndex])
  const goNext = useCallback(() => goToMove(Math.min(moveHistory.length - 1, activeMoveIndex + 1)), [goToMove, activeMoveIndex, moveHistory])

  return (
    <div className="min-h-screen flex" style={{ background: 'var(--bg-page)' }}>
      {/* ── Left Sidebar (Header converted to vertical) ──────────────── */}
      <div className="w-[140px] md:w-[200px] flex-shrink-0 border-r" style={{ background: 'var(--bg-sidebar)', borderColor: 'var(--border-default)' }}>
        <Header />
      </div>

      <main className="flex-1 flex items-center justify-center px-4 py-6 overflow-hidden">
        <div className="flex flex-col lg:flex-row items-center lg:items-start gap-8 animate-slide-up w-full max-w-[1200px] justify-center">

          {/* ── Board Column ────────────────────────────── */}
          <div className="flex flex-col" style={{ width: '100%', maxWidth: '640px' }}>
            <PlayerBar
              name="Chess Engine Bot"
              subtitle="AI (2500)"
              color="b"
              isActive={game.turn() === 'b'}
              captured={captured.b}
              materialDiff={materialDiff < 0 ? Math.abs(materialDiff) : 0}
              isThinking={status === 'ai-thinking'}
            />

            <div className="rounded-sm overflow-hidden" style={{ boxShadow: '0 4px 14px rgba(0,0,0,0.5)' }}>
              <ChessBoard
                position={boardPosition}
                onDrop={onDrop}
                lastMove={lastMove}
              />
            </div>

            <PlayerBar
              name="Guest"
              subtitle="Player"
              color="w"
              isActive={game.turn() === 'w' && status !== 'game-over'}
              captured={captured.w}
              materialDiff={materialDiff > 0 ? materialDiff : 0}
              isBottom
            />
          </div>

          {/* ── Side Panel ──────────────────────────────── */}
          <div className="w-full lg:w-[350px] flex-shrink-0 flex flex-col rounded-md overflow-hidden" style={{ background: 'var(--bg-card)', minHeight: '500px' }}>
            <SidePanel
              moves={moveHistory}
              activeMoveIndex={activeMoveIndex}
              status={status}
              gameResult={gameResult}
              inCheck={game.inCheck()}
              turn={game.turn()}
              onNewGame={resetGame}
              goFirst={goFirst}
              goPrev={goPrev}
              goNext={goNext}
              goLast={goLast}
              goToMove={goToMove}
              onResign={resignGame}
            />
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
