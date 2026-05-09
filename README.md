# Chess-AI ♟️

A full-stack, AI-powered chess application featuring a custom neural network, a robust classical evaluation engine, and a modern React frontend inspired by Chess.com aesthetics.

## Features

- **Hybrid AI Engine**: Combines a trained Neural Network (positional intuition) with a Classical Evaluation engine (Piece-Square Tables, King Safety, Mobility).
- **Advanced Search Algorithms**:
  - Iterative Deepening
  - Alpha-Beta Pruning with Move Ordering (MVV-LVA, Killer Moves)
  - Quiescence Search to avoid the horizon effect
  - Transposition Tables for performance
- **Opening Book**: Instantly plays standard opening theory for the first few moves.
- **Modern React Frontend**:
  - Built with Vite, React, and `react-chessboard` (v5).
  - Drag-and-drop and Click-to-move support with valid move detection.
  - Smooth animations, move history panel, and real-time AI "Thinking" indicators.
  - Responsive, dark-themed UI.

## Tech Stack

- **Frontend**: React, Vite, Tailwind CSS (Design System)
- **Backend**: FastAPI, Python, PyTorch (for the Neural Network), `python-chess`

## Installation and Setup

### 1. Backend (FastAPI + AI Engine)

```bash
# Navigate to the backend directory
cd chess-backend

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install the required dependencies
pip install fastapi uvicorn python-chess torch numpy pydantic

# Run the backend server
uvicorn main:app --reload --port 8000
```
*The API will be running at `http://127.0.0.1:8000`*

### 2. Frontend (React + Vite)

```bash
# Open a new terminal and navigate to the frontend directory
cd chess-frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```
*The Web App will be running at `http://localhost:5175`*

## How to Play

1. Ensure both the backend and frontend servers are running.
2. Open your browser and navigate to `http://localhost:5175`.
3. You play as White. Click or drag a piece to make a move.
4. The AI (Black) will automatically calculate its best move and respond!

## Neural Network Checkpoint

This engine currently runs on a custom-trained Value Network (loaded from `chess_model_checkpoint_9000.pth`). The model evaluates the win probability of a given board position, which works in tandem with the classical evaluation engine to find the strongest moves.
