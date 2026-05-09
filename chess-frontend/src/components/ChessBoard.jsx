import { useState, useRef, useCallback, useEffect } from 'react'
import { Chessboard } from 'react-chessboard'

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

  // Shared click-to-move logic
  // onPieceClick fires first, then onSquareClick bubbles - we only process the first
  const handleClickOnSquare = useCallback((square) => {
    if (processingClickRef.current) return
    processingClickRef.current = true
    // Reset at end of current event loop
    requestAnimationFrame(() => { processingClickRef.current = false })

    if (selectedSquare) {
      if (selectedSquare !== square) {
        const moveResult = onDrop(selectedSquare, square, null)
        if (moveResult) {
          setSelectedSquare(null)
          return
        }
      }
      // Same square or invalid move — deselect
      setSelectedSquare(null)
      return
    }
    // First click — select
    setSelectedSquare(square)
  }, [selectedSquare, onDrop])

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
