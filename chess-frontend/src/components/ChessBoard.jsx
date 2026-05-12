import { useState, useRef, useCallback, useEffect } from 'react'
import { Chessboard } from 'react-chessboard'
import { Chess } from 'chess.js'

export default function ChessBoard({ position, onDrop, lastMove }) {
  const [selectedSquare, setSelectedSquare] = useState(null)
  const processingClickRef = useRef(false)

  const squareStyles = {}

  // Highlight last move
  if (lastMove) {
    squareStyles[lastMove.from] = {
      background: 'rgba(255, 255, 0, 0.2)',
    }
    squareStyles[lastMove.to] = {
      background: 'rgba(255, 255, 0, 0.35)',
    }
  }

  // Highlight selected square and its legal moves
  if (selectedSquare) {
    squareStyles[selectedSquare] = {
      ...squareStyles[selectedSquare],
      background: 'rgba(255, 255, 0, 0.4)',
    }

    try {
      const g = new Chess(position)
      const moves = g.moves({ square: selectedSquare, verbose: true })
      
      moves.forEach((move) => {
        const isCapture = g.get(move.to) !== null || (g.get(selectedSquare).type === 'p' && move.to[0] !== selectedSquare[0]) // capture or en passant
        
        squareStyles[move.to] = {
          ...squareStyles[move.to],
          background: isCapture
            ? 'radial-gradient(circle, transparent 78%, rgba(0,0,0,0.2) 78%, rgba(0,0,0,0.2) 85%, transparent 85%)'
            : 'radial-gradient(circle, rgba(0,0,0,0.25) 10%, transparent 10%)',
          cursor: 'pointer',
        }
      })
    } catch (e) {
      // Ignore errors if position is invalid
    }
  }

  // Clear selectedSquare when position changes (new move was made)
  useEffect(() => {
    setSelectedSquare(null)
  }, [position])

  // Check if a square has a friendly piece
  const hasFriendlyPiece = useCallback((sq) => {
    try {
      const g = new Chess(position)
      const piece = g.get(sq)
      return piece && piece.color === g.turn()
    } catch (err) {
      return false
    }
  }, [position])

  // Shared click-to-move logic
  const handleClickOnSquare = useCallback((sq) => {
    if (processingClickRef.current) return
    processingClickRef.current = true
    requestAnimationFrame(() => { processingClickRef.current = false })

    if (selectedSquare) {
      if (selectedSquare === sq) {
        setSelectedSquare(null)
        return
      }
      // If clicking another friendly piece, switch selection
      if (hasFriendlyPiece(sq)) {
        setSelectedSquare(sq)
        return
      }
      // Try to move to the target square
      onDrop(selectedSquare, sq, null)
      setSelectedSquare(null)
      return
    }

    // First click — select only if it's a friendly piece
    if (hasFriendlyPiece(sq)) {
      setSelectedSquare(sq)
    }
  }, [selectedSquare, onDrop, hasFriendlyPiece])

  return (
    <div style={{ width: '100%', aspectRatio: '1' }}>
      <Chessboard
        options={{
          id: 'main-board',
          position: position,
          onPieceDrop: ({ sourceSquare, targetSquare }) => {
            setSelectedSquare(null)
            if (!sourceSquare || !targetSquare) return false
            return onDrop(sourceSquare, targetSquare, null)
          },
          onPieceClick: ({ square }) => {
            handleClickOnSquare(square)
          },
          onSquareClick: ({ square }) => {
            handleClickOnSquare(square)
          },
          animationDurationInMs: 200,
          dragActivationDistance: 5,
          boardStyle: {
            borderRadius: '0',
          },
          darkSquareStyle: { backgroundColor: '#779556' },
          lightSquareStyle: { backgroundColor: '#ebecd0' },
          squareStyles: squareStyles,
          dropSquareStyle: {
            boxShadow: 'inset 0 0 1px 5px rgba(255, 255, 0, 0.4)',
          },
        }}
      />
    </div>
  )
}
