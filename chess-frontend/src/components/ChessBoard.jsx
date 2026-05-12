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

  // Highlight selected square
  if (selectedSquare) {
    squareStyles[selectedSquare] = {
      background: 'rgba(255, 255, 0, 0.4)',
    }
  }

  // Clear selectedSquare when position changes (new move was made)
  useEffect(() => {
    setSelectedSquare(null)
  }, [position])

  // Check if a square has a friendly piece (white, since player is always white)
  const hasFriendlyPiece = useCallback((square) => {
    try {
      const g = new Chess(position)
      const piece = g.get(square)
      return piece && piece.color === g.turn()
    } catch {
      return false
    }
  }, [position])

  // Shared click-to-move logic
  const handleClickOnSquare = useCallback((square) => {
    if (processingClickRef.current) return
    processingClickRef.current = true
    requestAnimationFrame(() => { processingClickRef.current = false })

    if (selectedSquare) {
      if (selectedSquare === square) {
        // Same square — deselect
        setSelectedSquare(null)
        return
      }

      // If clicking another friendly piece, switch selection instead of trying to move
      if (hasFriendlyPiece(square)) {
        setSelectedSquare(square)
        return
      }

      // Try to move to the target square
      const moveResult = onDrop(selectedSquare, square, null)
      setSelectedSquare(null)
      if (moveResult) return

      // Invalid move — deselect
      return
    }

    // First click — select only if it's a friendly piece
    if (hasFriendlyPiece(square)) {
      setSelectedSquare(square)
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
