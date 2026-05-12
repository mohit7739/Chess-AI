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
  const [status, setStatus] = useState('your-turn')
  const [gameResult, setGameResult] = useState(null)
  const [lastMove, setLastMove] = useState(null)
  const [activeMoveIndex, setActiveMoveIndex] = useState(-1)
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
    if (status === 'ai-thinking' || status === 'game-over') return false

    const g = new Chess(game.fen())

    // Detect promotion: check piece param (drag-and-drop) or the piece on the source square (click-to-move)
    let isPromotion = false
    if (piece) {
      // piece is like 'wP' or 'bP'
      const pieceType = typeof piece === 'string' ? piece : piece?.pieceType
      isPromotion = pieceType?.[1] === 'P' && (targetSquare[1] === '8' || targetSquare[1] === '1')
    } else {
      // Click-to-move: check what's on the source square
      const srcPiece = g.get(sourceSquare)
      isPromotion = srcPiece?.type === 'p' && (targetSquare[1] === '8' || targetSquare[1] === '1')
    }
    const promotion = isPromotion ? 'q' : undefined

    const move = g.move({ from: sourceSquare, to: targetSquare, promotion })
    if (move === null) return false

    setGame(g)
    setBoardPosition(g.fen())
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
  }, [game, status, requestAIMove, updateStatus])

  const resetGame = useCallback(() => {
    const g = new Chess()
    setGame(g)
    setBoardPosition(g.fen())
    setMoveHistory([])
    setStatus('your-turn')
    setGameResult(null)
    setLastMove(null)
    setActiveMoveIndex(-1)
    aiThinking.current = false
  }, [])

  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--bg-page)' }}>
      <Header />

      <main className="flex-1 flex items-center justify-center px-3 py-4">
        <div className="flex flex-col lg:flex-row items-center lg:items-stretch gap-0 animate-slide-up">

          {/* ── Board Column ────────────────────────────── */}
          <div className="flex flex-col" style={{ width: '520px', maxWidth: '90vw' }}>
            {/* Opponent (Black) player bar */}
            <PlayerBar
              name="Chess Engine"
              subtitle="AI"
              color="b"
              isActive={game.turn() === 'b'}
              captured={captured.b}
              materialDiff={materialDiff < 0 ? Math.abs(materialDiff) : 0}
              isThinking={status === 'ai-thinking'}
            />

            {/* Board */}
            <ChessBoard
              position={boardPosition}
              onDrop={onDrop}
              lastMove={lastMove}
            />

            {/* You (White) player bar */}
            <PlayerBar
              name="You"
              subtitle="Player"
              color="w"
              isActive={game.turn() === 'w' && status !== 'game-over'}
              captured={captured.w}
              materialDiff={materialDiff > 0 ? materialDiff : 0}
              isBottom
            />
          </div>

          {/* ── Side Panel ──────────────────────────────── */}
          <SidePanel
            moves={moveHistory}
            activeMoveIndex={activeMoveIndex}
            status={status}
            gameResult={gameResult}
            inCheck={game.inCheck()}
            turn={game.turn()}
            onNewGame={resetGame}
          />
        </div>
      </main>
    </div>
  )
}

export default App
