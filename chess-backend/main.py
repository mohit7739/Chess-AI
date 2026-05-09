from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chess
import torch
import numpy as np
import torch.nn as nn
import os
import time
import random
import hashlib

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ─── Neural Network ───────────────────────────────────────────────
class ChessNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(768, 1024)
        self.fc2 = nn.Linear(1024, 512)
        self.fc3 = nn.Linear(512, 1)
        self.relu = nn.ReLU()
        self.sigmoid = nn.Sigmoid()
    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        return self.sigmoid(self.fc3(x))

device = torch.device("cpu")
model = ChessNet().to(device)
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'chess_model_checkpoint_9000.pth')
model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
model.eval()
print("✅ AI brain loaded (checkpoint 9000)")

# NN evaluation cache
nn_cache = {}
MAX_NN_CACHE = 100000

def fen_to_tensor(fen):
    board = chess.Board(fen)
    tensor = np.zeros(768, dtype=np.float32)
    piece_map = {chess.PAWN: 0, chess.KNIGHT: 1, chess.BISHOP: 2, chess.ROOK: 3, chess.QUEEN: 4, chess.KING: 5}
    for sq in chess.SQUARES:
        p = board.piece_at(sq)
        if p:
            offset = 0 if p.color == chess.WHITE else 6
            tensor[(piece_map[p.piece_type] + offset) * 64 + sq] = 1.0
    return tensor

def nn_eval(board):
    key = board.board_fen()
    if key in nn_cache:
        return nn_cache[key]
    if len(nn_cache) > MAX_NN_CACHE:
        nn_cache.clear()
    t = torch.tensor(fen_to_tensor(board.fen())).unsqueeze(0).to(device)
    with torch.no_grad():
        result = model(t).item()
    nn_cache[key] = result
    return result

# ─── Piece-Square Tables (midgame) ────────────────────────────────
PAWN_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0
]
KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
]
BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20
]
ROOK_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  0,  5,  5,  0,  0,  0
]
QUEEN_TABLE = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
]
KING_MID_TABLE = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20
]
KING_END_TABLE = [
    -50,-40,-30,-20,-20,-30,-40,-50,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-30,  0,  0,  0,  0,-30,-30,
    -50,-30,-30,-30,-30,-30,-30,-50
]

PST = {
    chess.PAWN: PAWN_TABLE, chess.KNIGHT: KNIGHT_TABLE,
    chess.BISHOP: BISHOP_TABLE, chess.ROOK: ROOK_TABLE,
    chess.QUEEN: QUEEN_TABLE, chess.KING: KING_MID_TABLE
}
PIECE_VALUES = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330, chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0}

def is_endgame(board):
    queens = len(board.pieces(chess.QUEEN, chess.WHITE)) + len(board.pieces(chess.QUEEN, chess.BLACK))
    minors = sum(len(board.pieces(pt, c)) for pt in [chess.KNIGHT, chess.BISHOP, chess.ROOK] for c in [chess.WHITE, chess.BLACK])
    return queens == 0 or (queens <= 2 and minors <= 4)

def classical_eval(board):
    """Strong handcrafted evaluation with material + positional + safety."""
    if board.is_checkmate():
        return -30000 if board.turn == chess.WHITE else 30000
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    endgame = is_endgame(board)
    score = 0

    # Material + piece-square tables
    for sq in chess.SQUARES:
        p = board.piece_at(sq)
        if not p:
            continue
        val = PIECE_VALUES[p.piece_type]
        if p.piece_type == chess.KING and endgame:
            pst_val = KING_END_TABLE[sq if p.color == chess.WHITE else chess.square_mirror(sq)]
        else:
            table = PST[p.piece_type]
            pst_val = table[sq if p.color == chess.WHITE else chess.square_mirror(sq)]
        total = val + pst_val
        score += total if p.color == chess.WHITE else -total

    # Bishop pair bonus
    if len(board.pieces(chess.BISHOP, chess.WHITE)) >= 2:
        score += 50
    if len(board.pieces(chess.BISHOP, chess.BLACK)) >= 2:
        score -= 50

    # Lightweight mobility: just check if side to move has more attackers on center
    for sq in [chess.E4, chess.D4, chess.E5, chess.D5]:
        w_att = len(board.attackers(chess.WHITE, sq))
        b_att = len(board.attackers(chess.BLACK, sq))
        score += (w_att - b_att) * 5

    # Center control
    center = [chess.E4, chess.D4, chess.E5, chess.D5]
    for sq in center:
        p = board.piece_at(sq)
        if p:
            score += 15 if p.color == chess.WHITE else -15

    # King safety — penalize open files near king
    for color in [chess.WHITE, chess.BLACK]:
        king_sq = board.king(color)
        if king_sq is not None:
            king_file = chess.square_file(king_sq)
            # Pawn shield
            shield = 0
            for f in range(max(0, king_file - 1), min(8, king_file + 2)):
                for r in range(8):
                    sq2 = chess.square(f, r)
                    p2 = board.piece_at(sq2)
                    if p2 and p2.piece_type == chess.PAWN and p2.color == color:
                        shield += 10
                        break
            if color == chess.WHITE:
                score += shield
            else:
                score -= shield

    return score

def hybrid_eval(board):
    """Combine classical evaluation with neural network for best of both worlds."""
    classical = classical_eval(board)
    nn_score = nn_eval(board)
    nn_centipawns = (nn_score - 0.5) * 600
    # Weight: 90% classical (fast + reliable), 10% NN (positional tiebreaker)
    return classical * 0.9 + nn_centipawns * 0.1

# ─── Transposition Table ──────────────────────────────────────────
TT_EXACT, TT_ALPHA, TT_BETA = 0, 1, 2
tt = {}
MAX_TT_SIZE = 500000

def tt_key(board):
    return board.fen()

def tt_store(board, depth, score, flag, best_move=None):
    if len(tt) > MAX_TT_SIZE:
        tt.clear()
    tt[tt_key(board)] = (depth, score, flag, best_move)

def tt_lookup(board, depth, alpha, beta):
    key = tt_key(board)
    if key not in tt:
        return None, None
    d, score, flag, best_move = tt[key]
    if d >= depth:
        if flag == TT_EXACT:
            return score, best_move
        elif flag == TT_ALPHA and score <= alpha:
            return alpha, best_move
        elif flag == TT_BETA and score >= beta:
            return beta, best_move
    return None, best_move  # Return best_move for ordering even if depth insufficient

# ─── Move Ordering ────────────────────────────────────────────────
MVV_LVA = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 100}
killer_moves = {}  # depth -> [move1, move2]

def score_move(board, move, tt_move, depth):
    """Score moves for ordering: higher = search first."""
    if move == tt_move:
        return 10000  # TT move first
    if board.is_capture(move):
        victim = board.piece_at(move.to_square)
        attacker = board.piece_at(move.from_square)
        if victim and attacker:
            return 5000 + MVV_LVA.get(victim.piece_type, 0) * 10 - MVV_LVA.get(attacker.piece_type, 0)
        return 5000
    if move.promotion:
        return 6000
    if board.gives_check(move):
        return 4500
    # Killer move heuristic
    if depth in killer_moves and move in killer_moves[depth]:
        return 4000
    # Prefer central moves
    to_file = chess.square_file(move.to_square)
    to_rank = chess.square_rank(move.to_square)
    center_bonus = max(0, 3 - abs(to_file - 3)) + max(0, 3 - abs(to_rank - 3))
    return center_bonus * 10

def ordered_moves(board, tt_move=None, depth=0):
    moves = list(board.legal_moves)
    moves.sort(key=lambda m: score_move(board, m, tt_move, depth), reverse=True)
    return moves

def store_killer(depth, move):
    if depth not in killer_moves:
        killer_moves[depth] = []
    if move not in killer_moves[depth]:
        killer_moves[depth].insert(0, move)
        if len(killer_moves[depth]) > 2:
            killer_moves[depth].pop()

# ─── Quiescence Search ────────────────────────────────────────────
def quiescence(board, alpha, beta, is_white, depth=0):
    """Search captures/checks until position is quiet. Uses fast classical eval."""
    stand_pat = classical_eval(board)
    if is_white:
        if stand_pat >= beta:
            return beta
        alpha = max(alpha, stand_pat)
        for move in board.legal_moves:
            if not (board.is_capture(move) or (depth < 2 and board.gives_check(move))):
                continue
            board.push(move)
            score = quiescence(board, alpha, beta, False, depth + 1)
            board.pop()
            if score >= beta:
                return beta
            alpha = max(alpha, score)
        return alpha
    else:
        if stand_pat <= alpha:
            return alpha
        beta = min(beta, stand_pat)
        for move in board.legal_moves:
            if not (board.is_capture(move) or (depth < 2 and board.gives_check(move))):
                continue
            board.push(move)
            score = quiescence(board, alpha, beta, True, depth + 1)
            board.pop()
            if score <= alpha:
                return alpha
            beta = min(beta, score)
        return beta

# ─── Alpha-Beta with Enhancements ─────────────────────────────────
nodes_searched = 0

def alphabeta(board, depth, alpha, beta, is_white, allow_null=True):
    global nodes_searched
    nodes_searched += 1

    # Check TT
    tt_score, tt_move = tt_lookup(board, depth, alpha, beta)
    if tt_score is not None:
        return tt_score

    if board.is_game_over():
        if board.is_checkmate():
            return -30000 - depth if board.turn == chess.WHITE else 30000 + depth
        return 0

    if depth <= 0:
        return quiescence(board, alpha, beta, is_white)

    # Null-move pruning (skip if in check or endgame)
    if allow_null and depth >= 3 and not board.is_check() and not is_endgame(board):
        board.push(chess.Move.null())
        null_score = alphabeta(board, depth - 3, alpha, beta, not is_white, False)
        board.pop()
        if is_white and null_score >= beta:
            return beta
        if not is_white and null_score <= alpha:
            return alpha

    moves = ordered_moves(board, tt_move, depth)
    best_move = moves[0] if moves else None
    orig_alpha = alpha

    if is_white:
        max_eval = -float('inf')
        for i, move in enumerate(moves):
            board.push(move)
            # Late Move Reduction
            if i >= 4 and depth >= 3 and not board.is_capture(move) and not board.is_check():
                score = alphabeta(board, depth - 2, alpha, beta, False)
                if score > alpha:
                    score = alphabeta(board, depth - 1, alpha, beta, False)
            else:
                score = alphabeta(board, depth - 1, alpha, beta, False)
            board.pop()
            if score > max_eval:
                max_eval = score
                best_move = move
            alpha = max(alpha, score)
            if beta <= alpha:
                store_killer(depth, move)
                break
        # Store in TT
        if max_eval <= orig_alpha:
            tt_store(board, depth, max_eval, TT_ALPHA, best_move)
        elif max_eval >= beta:
            tt_store(board, depth, max_eval, TT_BETA, best_move)
        else:
            tt_store(board, depth, max_eval, TT_EXACT, best_move)
        return max_eval
    else:
        min_eval = float('inf')
        for i, move in enumerate(moves):
            board.push(move)
            if i >= 4 and depth >= 3 and not board.is_capture(move) and not board.is_check():
                score = alphabeta(board, depth - 2, alpha, beta, True)
                if score < beta:
                    score = alphabeta(board, depth - 1, alpha, beta, True)
            else:
                score = alphabeta(board, depth - 1, alpha, beta, True)
            board.pop()
            if score < min_eval:
                min_eval = score
                best_move = move
            beta = min(beta, score)
            if beta <= alpha:
                store_killer(depth, move)
                break
        if min_eval >= beta:
            tt_store(board, depth, min_eval, TT_BETA, best_move)
        elif min_eval <= orig_alpha:
            tt_store(board, depth, min_eval, TT_ALPHA, best_move)
        else:
            tt_store(board, depth, min_eval, TT_EXACT, best_move)
        return min_eval

# ─── Iterative Deepening ──────────────────────────────────────────
def find_best_move(board, max_time=4.0, max_depth=8):
    """Iterative deepening with time control — thinks deeper when it has time."""
    global nodes_searched
    nodes_searched = 0
    killer_moves.clear()

    is_white = board.turn == chess.WHITE
    best_move = None
    best_score = None
    start = time.time()

    for depth in range(1, max_depth + 1):
        elapsed = time.time() - start
        if depth > 2 and elapsed > max_time * 0.6:
            break  # Don't start a new depth if >60% time used

        alpha = -float('inf')
        beta = float('inf')
        current_best = None
        current_score = -float('inf') if is_white else float('inf')

        moves = ordered_moves(board, best_move, depth)

        for move in moves:
            if time.time() - start > max_time:
                break
            board.push(move)
            score = alphabeta(board, depth - 1, alpha, beta, not is_white)
            board.pop()

            if is_white:
                if score > current_score:
                    current_score = score
                    current_best = move
                alpha = max(alpha, score)
            else:
                if score < current_score:
                    current_score = score
                    current_best = move
                beta = min(beta, score)

        if current_best:
            best_move = current_best
            best_score = current_score

        elapsed = time.time() - start
        print(f"  depth {depth}: {best_move.uci() if best_move else '?'} ({best_score:.0f}) [{nodes_searched} nodes, {elapsed:.1f}s]")

        if time.time() - start > max_time:
            break

    return best_move, best_score

# ─── Opening Book ─────────────────────────────────────────────────
OPENING_BOOK = {
    # Starting position responses
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w": ["e2e4", "d2d4", "c2c4", "g1f3"],
    # After 1.e4
    "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b": ["e7e5", "c7c5", "e7e6", "c7c6", "d7d5"],
    # After 1.d4
    "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b": ["d7d5", "g8f6", "e7e6", "f7f5"],
    # After 1.e4 e5
    "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w": ["g1f3", "f1c4", "b1c3"],
    # After 1.e4 e5 2.Nf3
    "rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b": ["b8c6", "g8f6", "d7d6"],
    # After 1.e4 c5 (Sicilian)
    "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w": ["g1f3", "b1c3", "c2c3"],
    # After 1.d4 d5
    "rnbqkbnr/ppp1pppp/8/3p4/3P4/8/PPP1PPPP/RNBQKBNR w": ["c2c4", "g1f3", "b1c3", "c1f4"],
    # After 1.d4 Nf6
    "rnbqkb1r/pppppppp/5n2/8/3P4/8/PPP1PPPP/RNBQKBNR w": ["c2c4", "g1f3", "c1g5"],
    # After 1.e4 e5 2.Nf3 Nc6
    "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w": ["f1b5", "f1c4", "d2d4"],
    # Italian Game
    "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b": ["f8c5", "g8f6", "f7f5"],
    # Ruy Lopez
    "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b": ["a7a6", "g8f6", "f7f5"],
    # Queen's Gambit
    "rnbqkbnr/ppp1pppp/8/3p4/2PP4/8/PP2PPPP/RNBQKBNR b": ["d5c4", "e7e6", "c7c6", "e7e5"],
    # After 1.Nf3
    "rnbqkbnr/pppppppp/8/8/8/5N2/PPPPPPPP/RNBQKB1R b": ["d7d5", "g8f6", "c7c5"],
    # After 1.c4 (English)
    "rnbqkbnr/pppppppp/8/8/2P5/8/PP1PPPPP/RNBQKBNR b": ["e7e5", "g8f6", "c7c5"],
}

def get_book_move(board):
    fen_key = " ".join(board.fen().split()[:2])  # position + turn only
    if fen_key in OPENING_BOOK:
        candidates = OPENING_BOOK[fen_key]
        legal_ucis = [m.uci() for m in board.legal_moves]
        valid = [m for m in candidates if m in legal_ucis]
        if valid:
            # Weighted random: prefer first entries
            weights = [3, 2, 1, 1, 1][:len(valid)]
            return random.choices(valid, weights=weights)[0]
    return None

# ─── API ──────────────────────────────────────────────────────────
class MoveRequest(BaseModel):
    fen: str
    time_limit: float = 4.0
    max_depth: int = 8

@app.post("/api/get-move")
async def get_move(request: MoveRequest):
    try:
        board = chess.Board(request.fen)
        if board.is_game_over():
            return {"error": "Game is already over"}

        # Try opening book first
        book_move = get_book_move(board)
        if book_move:
            print(f"📖 Book move: {book_move}")
            return {"move": book_move, "source": "book"}

        # Otherwise, think with iterative deepening
        print(f"🤔 Thinking... (max {request.time_limit}s, depth {request.max_depth})")
        best_move, score = find_best_move(board, request.time_limit, request.max_depth)

        if best_move is None:
            return {"error": "No legal moves"}

        print(f"✅ Best: {best_move.uci()} (score: {score:.0f})")
        return {"move": best_move.uci(), "score": round(score, 1), "source": "engine"}
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"error": str(e)}

@app.get("/")
async def root():
    return {"status": "Chess AI Engine v2.0 — Hybrid NN + Classical", "features": [
        "Iterative deepening (up to depth 8)",
        "Alpha-beta with null-move pruning",
        "Quiescence search",
        "Transposition table",
        "Move ordering (MVV-LVA + killer moves)",
        "Opening book",
        "Hybrid evaluation (classical + neural network)"
    ]}