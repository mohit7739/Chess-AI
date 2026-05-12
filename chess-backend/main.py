from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chess, torch, numpy as np, torch.nn as nn, os, random, time

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class ChessNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(768, 1024)
        self.fc2 = nn.Linear(1024, 512)
        self.fc3 = nn.Linear(512, 1)
        self.relu = nn.ReLU()
        self.sigmoid = nn.Sigmoid()
    def forward(self, x):
        return self.sigmoid(self.fc3(self.relu(self.fc2(self.relu(self.fc1(x))))))

device = torch.device("cpu")
model = ChessNet().to(device)
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'chess_model_checkpoint_9000.pth')
model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
model.eval()
print("✅ AI loaded")

nn_cache = {}
def fen_to_tensor(fen):
    board = chess.Board(fen)
    t = np.zeros(768, dtype=np.float32)
    pm = {chess.PAWN:0,chess.KNIGHT:1,chess.BISHOP:2,chess.ROOK:3,chess.QUEEN:4,chess.KING:5}
    for sq in chess.SQUARES:
        p = board.piece_at(sq)
        if p:
            t[(pm[p.piece_type]+(0 if p.color==chess.WHITE else 6))*64+sq]=1.0
    return t

def nn_eval(board):
    k = board.board_fen()
    if k in nn_cache: return nn_cache[k]
    if len(nn_cache)>100000: nn_cache.clear()
    with torch.no_grad():
        r = model(torch.tensor(fen_to_tensor(board.fen())).unsqueeze(0).to(device)).item()
    nn_cache[k]=r
    return r

# Piece-Square Tables
PAWN_T=[0,0,0,0,0,0,0,0,50,50,50,50,50,50,50,50,10,10,20,30,30,20,10,10,5,5,10,25,25,10,5,5,0,0,0,20,20,0,0,0,5,-5,-10,0,0,-10,-5,5,5,10,10,-20,-20,10,10,5,0,0,0,0,0,0,0,0]
KNIGHT_T=[-50,-40,-30,-30,-30,-30,-40,-50,-40,-20,0,0,0,0,-20,-40,-30,0,10,15,15,10,0,-30,-30,5,15,20,20,15,5,-30,-30,0,15,20,20,15,0,-30,-30,5,10,15,15,10,5,-30,-40,-20,0,5,5,0,-20,-40,-50,-40,-30,-30,-30,-30,-40,-50]
BISHOP_T=[-20,-10,-10,-10,-10,-10,-10,-20,-10,0,0,0,0,0,0,-10,-10,0,10,10,10,10,0,-10,-10,5,5,10,10,5,5,-10,-10,0,10,10,10,10,0,-10,-10,10,10,10,10,10,10,-10,-10,5,0,0,0,0,5,-10,-20,-10,-10,-10,-10,-10,-10,-20]
ROOK_T=[0,0,0,0,0,0,0,0,5,10,10,10,10,10,10,5,-5,0,0,0,0,0,0,-5,-5,0,0,0,0,0,0,-5,-5,0,0,0,0,0,0,-5,-5,0,0,0,0,0,0,-5,-5,0,0,0,0,0,0,-5,0,0,0,5,5,0,0,0]
QUEEN_T=[-20,-10,-10,-5,-5,-10,-10,-20,-10,0,0,0,0,0,0,-10,-10,0,5,5,5,5,0,-10,-5,0,5,5,5,5,0,-5,0,0,5,5,5,5,0,-5,-10,5,5,5,5,5,0,-10,-10,0,5,0,0,0,0,-10,-20,-10,-10,-5,-5,-10,-10,-20]
KING_MID=[-30,-40,-40,-50,-50,-40,-40,-30,-30,-40,-40,-50,-50,-40,-40,-30,-30,-40,-40,-50,-50,-40,-40,-30,-30,-40,-40,-50,-50,-40,-40,-30,-20,-30,-30,-40,-40,-30,-30,-20,-10,-20,-20,-20,-20,-20,-20,-10,20,20,0,0,0,0,20,20,20,30,10,0,0,10,30,20]
KING_END=[-50,-40,-30,-20,-20,-30,-40,-50,-30,-20,-10,0,0,-10,-20,-30,-30,-10,20,30,30,20,-10,-30,-30,-10,30,40,40,30,-10,-30,-30,-10,30,40,40,30,-10,-30,-30,-10,20,30,30,20,-10,-30,-30,-30,0,0,0,0,-30,-30,-50,-30,-30,-30,-30,-30,-30,-50]

PST={chess.PAWN:PAWN_T,chess.KNIGHT:KNIGHT_T,chess.BISHOP:BISHOP_T,chess.ROOK:ROOK_T,chess.QUEEN:QUEEN_T,chess.KING:KING_MID}
PV={chess.PAWN:100,chess.KNIGHT:320,chess.BISHOP:330,chess.ROOK:500,chess.QUEEN:900,chess.KING:0}
MVV={chess.PAWN:1,chess.KNIGHT:3,chess.BISHOP:3,chess.ROOK:5,chess.QUEEN:9,chess.KING:100}

def is_endgame(b):
    q=len(b.pieces(chess.QUEEN,chess.WHITE))+len(b.pieces(chess.QUEEN,chess.BLACK))
    m=sum(len(b.pieces(pt,c)) for pt in[chess.KNIGHT,chess.BISHOP,chess.ROOK] for c in[chess.WHITE,chess.BLACK])
    return q==0 or(q<=2 and m<=4)

def classical_eval(board):
    if board.is_checkmate(): return -29999 if board.turn==chess.WHITE else 29999
    if board.is_stalemate() or board.is_insufficient_material(): return 0
    if board.can_claim_fifty_moves(): return 0
    if board.is_repetition(2): return 0

    eg=is_endgame(board); s=0
    for sq in chess.SQUARES:
        p=board.piece_at(sq)
        if not p: continue
        v=PV[p.piece_type]
        mi=sq if p.color==chess.WHITE else chess.square_mirror(sq)
        if p.piece_type==chess.KING and eg: pv=KING_END[mi]
        else: pv=PST[p.piece_type][mi]
        t=v+pv
        s+=t if p.color==chess.WHITE else -t

    # Bishop pair
    if len(board.pieces(chess.BISHOP,chess.WHITE))>=2: s+=50
    if len(board.pieces(chess.BISHOP,chess.BLACK))>=2: s-=50
    # Rook on open file
    for c in[chess.WHITE,chess.BLACK]:
        for sq in board.pieces(chess.ROOK,c):
            f=chess.square_file(sq)
            has_own_pawn=any(board.piece_at(chess.square(f,r)) and board.piece_at(chess.square(f,r)).piece_type==chess.PAWN and board.piece_at(chess.square(f,r)).color==c for r in range(8))
            if not has_own_pawn:
                s+=(25 if c==chess.WHITE else -25)
    # Passed pawns
    for c in[chess.WHITE,chess.BLACK]:
        for sq in board.pieces(chess.PAWN,c):
            f=chess.square_file(sq); r=chess.square_rank(sq)
            passed=True
            for ef in range(max(0,f-1),min(8,f+2)):
                for er in range(8):
                    ep=board.piece_at(chess.square(ef,er))
                    if ep and ep.piece_type==chess.PAWN and ep.color!=c:
                        if(c==chess.WHITE and er>r)or(c==chess.BLACK and er<r):
                            passed=False; break
                if not passed: break
            if passed:
                bonus=20+10*(r if c==chess.WHITE else 7-r)
                s+=(bonus if c==chess.WHITE else -bonus)
    # Center control
    for sq in[chess.E4,chess.D4,chess.E5,chess.D5]:
        wa=len(board.attackers(chess.WHITE,sq)); ba=len(board.attackers(chess.BLACK,sq))
        s+=(wa-ba)*8
        p=board.piece_at(sq)
        if p: s+=(15 if p.color==chess.WHITE else -15)
    # King safety
    for c in[chess.WHITE,chess.BLACK]:
        ksq=board.king(c)
        if ksq is None: continue
        kf=chess.square_file(ksq); shield=0
        for f2 in range(max(0,kf-1),min(8,kf+2)):
            for r2 in range(8):
                pp=board.piece_at(chess.square(f2,r2))
                if pp and pp.piece_type==chess.PAWN and pp.color==c:
                    shield+=12; break
        # Penalize king on open file
        own_pawns_on_file=any(board.piece_at(chess.square(kf,r)) and board.piece_at(chess.square(kf,r)).piece_type==chess.PAWN and board.piece_at(chess.square(kf,r)).color==c for r in range(8))
        if not own_pawns_on_file and not eg: shield-=30
        s+=(shield if c==chess.WHITE else -shield)
    # Knight outpost
    for c in[chess.WHITE,chess.BLACK]:
        for sq in board.pieces(chess.KNIGHT,c):
            f=chess.square_file(sq); r=chess.square_rank(sq)
            if(c==chess.WHITE and r>=3 and r<=5)or(c==chess.BLACK and r>=2 and r<=4):
                supported=False
                for df in[-1,1]:
                    sf=f+df; sr=r+(-1 if c==chess.WHITE else 1)
                    if 0<=sf<8 and 0<=sr<8:
                        sp=board.piece_at(chess.square(sf,sr))
                        if sp and sp.piece_type==chess.PAWN and sp.color==c: supported=True
                if supported: s+=(25 if c==chess.WHITE else -25)
    # Repetition penalty — strongly discourage moves leading toward repetition
    if board.is_repetition(1): s = s * 0.5  # halve score if position repeated
    return s

# Transposition Table
TT_EXACT,TT_ALPHA,TT_BETA=0,1,2
tt={}
history_table={}  # history heuristic: (from,to) -> score

def tt_store(b,d,s,f,bm=None):
    if len(tt)>800000: tt.clear()
    tt[b.fen()]=(d,s,f,bm)

def tt_lookup(b,d,a,bt):
    k=b.fen()
    if k not in tt: return None,None
    dd,s,f,bm=tt[k]
    if dd>=d:
        if f==TT_EXACT: return s,bm
        elif f==TT_ALPHA and s<=a: return a,bm
        elif f==TT_BETA and s>=bt: return bt,bm
    return None,bm

killer_moves={}
def store_killer(d,m):
    if d not in killer_moves: killer_moves[d]=[]
    if m not in killer_moves[d]:
        killer_moves[d].insert(0,m)
        if len(killer_moves[d])>2: killer_moves[d].pop()

def score_move(b,m,ttm,d):
    if m==ttm: return 100000
    if m.promotion: return 60000+(9 if m.promotion==chess.QUEEN else 0)
    if b.is_capture(m):
        v=b.piece_at(m.to_square); a=b.piece_at(m.from_square)
        if v and a: return 50000+MVV.get(v.piece_type,0)*10-MVV.get(a.piece_type,0)
        return 50000
    if b.gives_check(m): return 45000
    if d in killer_moves and m in killer_moves[d]: return 40000
    hk=(m.from_square,m.to_square)
    return history_table.get(hk,0)

def ordered_moves(b,ttm=None,d=0):
    moves=list(b.legal_moves)
    moves.sort(key=lambda m:score_move(b,m,ttm,d),reverse=True)
    return moves

# Quiescence with delta pruning
def quiescence(b,a,bt,maximizing,d=0):
    sp=classical_eval(b)
    if maximizing:
        if sp>=bt: return bt
        if d>=6: return sp  # max quiescence depth
        a=max(a,sp)
        caps=sorted([m for m in b.legal_moves if b.is_capture(m) or(d<2 and b.gives_check(m))],
                     key=lambda m:MVV.get((b.piece_at(m.to_square) or type('',(),{'piece_type':0})).piece_type,0)*10-MVV.get((b.piece_at(m.from_square) or type('',(),{'piece_type':0})).piece_type,0),reverse=True)
        for m in caps:
            # Delta pruning
            if d>0 and not b.gives_check(m):
                v=b.piece_at(m.to_square)
                if v and sp+PV.get(v.piece_type,0)+200<a: continue
            b.push(m); s=quiescence(b,a,bt,False,d+1); b.pop()
            if s>=bt: return bt
            a=max(a,s)
        return a
    else:
        if sp<=a: return a
        if d>=6: return sp
        bt=min(bt,sp)
        caps=sorted([m for m in b.legal_moves if b.is_capture(m) or(d<2 and b.gives_check(m))],
                     key=lambda m:MVV.get((b.piece_at(m.to_square) or type('',(),{'piece_type':0})).piece_type,0)*10-MVV.get((b.piece_at(m.from_square) or type('',(),{'piece_type':0})).piece_type,0),reverse=True)
        for m in caps:
            if d>0 and not b.gives_check(m):
                v=b.piece_at(m.to_square)
                if v and sp-PV.get(v.piece_type,0)-200>bt: continue
            b.push(m); s=quiescence(b,a,bt,True,d+1); b.pop()
            if s<=a: return a
            bt=min(bt,s)
        return bt

nodes=0
stop_search=False
search_start=0
MAX_SEARCH_TIME=10.0

def alphabeta(b,d,a,bt,mx,null_ok=True):
    global nodes, stop_search
    nodes+=1
    # Check time every 1024 nodes
    if nodes & 1023 == 0 and time.time()-search_start > MAX_SEARCH_TIME:
        stop_search=True
    if stop_search: return 0
    ts,tm=tt_lookup(b,d,a,bt)
    if ts is not None: return ts

    if b.is_game_over():
        if b.is_checkmate(): return(-29999-d)if b.turn==chess.WHITE else(29999+d)
        return 0
    if b.can_claim_fifty_moves() or b.is_repetition(2): return 0

    if d<=0: return quiescence(b,a,bt,mx)

    in_check=b.is_check()
    # Check extension
    ext=1 if in_check else 0

    # Null-move pruning
    if null_ok and d>=3 and not in_check and not is_endgame(b):
        R=3 if d>=6 else 2
        b.push(chess.Move.null())
        ns=alphabeta(b,d-1-R,a,bt,not mx,False)
        b.pop()
        if mx and ns>=bt: return bt
        if not mx and ns<=a: return a

    moves=ordered_moves(b,tm,d)
    if not moves: return 0
    bm=moves[0]; oa=a

    if mx:
        me=-99999
        for i,m in enumerate(moves):
            b.push(m)
            # Extensions: check, recapture, pawn push to 7th
            e=ext
            p=b.piece_at(m.to_square) if not b.is_capture(m) else None
            src_p_type = b.piece_at(m.from_square).piece_type if b.piece_at(m.from_square) else None
            if not e:
                # Extend pawn pushes to 7th rank
                piece_moved = b.piece_at(m.to_square)
                if piece_moved and piece_moved.piece_type==chess.PAWN and chess.square_rank(m.to_square)>=6: e=1

            # PVS + LMR
            if i==0:
                s=alphabeta(b,d-1+e,a,bt,False)
            else:
                # Late move reduction
                if i>=4 and d>=3 and not b.is_capture(m) and not in_check and not b.is_check() and e==0:
                    s=alphabeta(b,d-2,a,a+1,False)  # null window reduced
                    if s>a: s=alphabeta(b,d-1+e,a,bt,False)  # re-search
                else:
                    s=alphabeta(b,d-1+e,a,a+1,False)  # null window
                    if a<s<bt: s=alphabeta(b,d-1+e,a,bt,False)  # re-search
            b.pop()
            if s>me: me=s; bm=m
            a=max(a,s)
            if bt<=a:
                if not b.is_capture(m):
                    store_killer(d,m)
                    hk=(m.from_square,m.to_square)
                    history_table[hk]=history_table.get(hk,0)+d*d
                break
        if me<=oa: tt_store(b,d,me,TT_ALPHA,bm)
        elif me>=bt: tt_store(b,d,me,TT_BETA,bm)
        else: tt_store(b,d,me,TT_EXACT,bm)
        return me
    else:
        me=99999
        for i,m in enumerate(moves):
            b.push(m)
            e=ext
            piece_moved = b.piece_at(m.to_square)
            if not e and piece_moved and piece_moved.piece_type==chess.PAWN and chess.square_rank(m.to_square)<=1: e=1

            if i==0:
                s=alphabeta(b,d-1+e,a,bt,True)
            else:
                if i>=4 and d>=3 and not b.is_capture(m) and not in_check and not b.is_check() and e==0:
                    s=alphabeta(b,d-2,bt-1,bt,True)
                    if s<bt: s=alphabeta(b,d-1+e,a,bt,True)
                else:
                    s=alphabeta(b,d-1+e,bt-1,bt,True)
                    if a<s<bt: s=alphabeta(b,d-1+e,a,bt,True)
            b.pop()
            if s<me: me=s; bm=m
            bt=min(bt,s)
            if bt<=a:
                if not b.is_capture(m):
                    store_killer(d,m)
                    hk=(m.from_square,m.to_square)
                    history_table[hk]=history_table.get(hk,0)+d*d
                break
        if me>=bt: tt_store(b,d,me,TT_BETA,bm)
        elif me<=oa: tt_store(b,d,me,TT_ALPHA,bm)
        else: tt_store(b,d,me,TT_EXACT,bm)
        return me

def find_best_move(board, max_depth=12):
    global nodes, stop_search, search_start
    nodes=0; stop_search=False; search_start=time.time()
    killer_moves.clear(); history_table.clear()
    is_w=board.turn==chess.WHITE; best=None; best_s=None

    for depth in range(1, max_depth+1):
        if stop_search or time.time()-search_start > MAX_SEARCH_TIME*0.6:
            break
        a=-99999; bt=99999; cb=None
        cs=-99999 if is_w else 99999
        moves=ordered_moves(board,best,depth)

        for m in moves:
            if stop_search: break
            board.push(m)
            s=alphabeta(board,depth-1,a,bt,not is_w)
            board.pop()
            if stop_search: break
            if is_w:
                if s>cs: cs=s; cb=m
                a=max(a,s)
            else:
                if s<cs: cs=s; cb=m
                bt=min(bt,s)

        if not stop_search and cb:
            best=cb; best_s=cs
        elapsed=time.time()-search_start
        score_str = f"{best_s:.0f}" if best_s is not None else "?"
        print(f"  d{depth}: {best.uci() if best else '?'} ({score_str}) [{nodes}n, {elapsed:.1f}s]")

        # Stop conditions
        if best_s is not None and(best_s>29000 or best_s<-29000): break
        if depth>=5 and nodes>100000: break
        if depth>=7 and nodes>50000: break

    return best, best_s

# Opening Book
BOOK={
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w":["e2e4","d2d4","c2c4","g1f3"],
    "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b":["e7e5","c7c5","e7e6","c7c6"],
    "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b":["d7d5","g8f6","e7e6"],
    "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w":["g1f3","f1c4","b1c3"],
    "rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b":["b8c6","g8f6"],
    "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w":["g1f3","b1c3","c2c3"],
    "rnbqkbnr/ppp1pppp/8/3p4/3P4/8/PPP1PPPP/RNBQKBNR w":["c2c4","g1f3","b1c3","c1f4"],
    "rnbqkb1r/pppppppp/5n2/8/3P4/8/PPP1PPPP/RNBQKBNR w":["c2c4","g1f3"],
    "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w":["f1b5","f1c4","d2d4"],
    "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b":["f8c5","g8f6"],
    "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b":["a7a6","g8f6"],
    "rnbqkbnr/ppp1pppp/8/3p4/2PP4/8/PP2PPPP/RNBQKBNR b":["d5c4","e7e6","c7c6"],
    "rnbqkbnr/pppppppp/8/8/8/5N2/PPPPPPPP/RNBQKB1R b":["d7d5","g8f6","c7c5"],
    "rnbqkbnr/pppppppp/8/8/2P5/8/PP1PPPPP/RNBQKBNR b":["e7e5","g8f6","c7c5"],
}

def get_book_move(b):
    k=" ".join(b.fen().split()[:2])
    if k in BOOK:
        legal=[m.uci() for m in b.legal_moves]
        valid=[m for m in BOOK[k] if m in legal]
        if valid: return random.choices(valid,weights=[3,2,1,1,1][:len(valid)])[0]
    return None

class MoveRequest(BaseModel):
    fen: str

# ─── Pondering (Pre-Think) System ─────────────────────────────────
import threading

ponder_lock = threading.Lock()
ponder_result = {"fen": None, "predicted_opponent_move": None, "response_move": None, "score": None}
ponder_thread = None

def ponder_worker(board_fen, ai_move_uci):
    """Background thread: predict opponent's best reply, then calculate our response."""
    global ponder_result
    try:
        b = chess.Board(board_fen)
        # Apply the AI move we just played
        b.push(chess.Move.from_uci(ai_move_uci))

        if b.is_game_over():
            return

        # Find opponent's most likely reply (search shallow & fast)
        opp_move, _ = find_best_move(b, max_depth=6)
        if opp_move is None:
            return

        # Now apply opponent's predicted move and find OUR response
        b.push(opp_move)
        if b.is_game_over():
            return

        # Check book first
        book = get_book_move(b)
        if book:
            with ponder_lock:
                ponder_result = {
                    "fen": b.fen(),
                    "predicted_opponent_move": opp_move.uci(),
                    "response_move": book,
                    "score": None
                }
            print(f"🔮 Ponder: if opponent plays {opp_move.uci()}, reply {book} (book)")
            return

        our_move, our_score = find_best_move(b, max_depth=8)
        if our_move:
            with ponder_lock:
                ponder_result = {
                    "fen": b.fen(),
                    "predicted_opponent_move": opp_move.uci(),
                    "response_move": our_move.uci(),
                    "score": our_score
                }
            print(f"🔮 Ponder: if opponent plays {opp_move.uci()}, reply {our_move.uci()} ({our_score:.0f})")
    except Exception as e:
        print(f"🔮 Ponder error: {e}")

def start_pondering(board_fen, ai_move_uci):
    """Start pondering in background after AI makes a move."""
    global ponder_thread, ponder_result
    with ponder_lock:
        ponder_result = {"fen": None, "predicted_opponent_move": None, "response_move": None, "score": None}
    ponder_thread = threading.Thread(target=ponder_worker, args=(board_fen, ai_move_uci), daemon=True)
    ponder_thread.start()

def check_ponder_hit(current_fen):
    """Check if the current position matches our ponder prediction."""
    with ponder_lock:
        if ponder_result["fen"] and ponder_result["fen"] == current_fen and ponder_result["response_move"]:
            return ponder_result["response_move"], ponder_result["score"]
    return None, None

@app.post("/api/get-move")
async def get_move(req: MoveRequest):
    try:
        b = chess.Board(req.fen)
        if b.is_game_over():
            return {"error": "Game over"}

        # Check if we pre-computed this position (ponder hit!)
        ponder_move, ponder_score = check_ponder_hit(req.fen)
        if ponder_move:
            # Verify it's still legal
            legal_ucis = [m.uci() for m in b.legal_moves]
            if ponder_move in legal_ucis:
                print(f"⚡ Ponder hit! Instant reply: {ponder_move}")
                start_pondering(req.fen, ponder_move)
                return {"move": ponder_move, "score": round(ponder_score, 1) if ponder_score else None, "source": "ponder"}

        # Try opening book
        bm = get_book_move(b)
        if bm:
            print(f"📖 {bm}")
            start_pondering(req.fen, bm)
            return {"move": bm, "source": "book"}

        # Full search
        print("🤔 Thinking...")
        mv, sc = find_best_move(b)
        if mv is None:
            return {"error": "No moves"}

        print(f"✅ {mv.uci()} ({sc:.0f})")
        # Start pondering our next move while human thinks
        start_pondering(req.fen, mv.uci())
        return {"move": mv.uci(), "score": round(sc, 1), "source": "engine"}
    except Exception as e:
        print(f"❌ {e}")
        return {"error": str(e)}

@app.get("/")
async def root():
    return {"status": "Chess AI v3.1 — Maximum Strength + Pondering", "features": [
        "Depth 12 iterative deepening with 10s time limit",
        "PVS + LMR + Null-move pruning",
        "Check/pawn extensions",
        "Quiescence with delta pruning",
        "History heuristic + killer moves",
        "Repetition avoidance + 50-move rule",
        "Pondering (pre-think while human is thinking)",
        "Opening book"
    ]}