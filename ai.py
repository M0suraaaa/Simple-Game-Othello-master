"""ai.py - Fungsi evaluasi, MiniMax, Alpha-Beta Pruning, dan statistik pencarian."""

import time

from board import (apply_move, count_discs, game_over, get_valid_moves)

WEIGHTS = [
    [100, -20, 10,  5,  5, 10, -20, 100],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [ 10,  -2, -1, -1, -1, -1,  -2,  10],
    [  5,  -2, -1, -1, -1, -1,  -2,   5],
    [  5,  -2, -1, -1, -1, -1,  -2,   5],
    [ 10,  -2, -1, -1, -1, -1,  -2,  10],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [100, -20, 10,  5,  5, 10, -20, 100],
]


# ---------------------------------------------------------------------------
# Statistik pencarian
# ---------------------------------------------------------------------------
class SearchStats:
    """
    Mencatat parameter pembanding untuk setiap langkah yang dipilih AI.

    Definisi:
      - simpul diperiksa : berapa kali fungsi pencarian dipanggil (satu panggilan
                           = satu keadaan papan yang dikunjungi) untuk satu langkah.
      - cabang dipotong  : jumlah langkah (cabang) yang TIDAK diperiksa karena
                           alpha >= beta. Yang dihitung cabang langsung yang
                           dilewati, bukan seluruh turunannya. MiniMax murni
                           selalu bernilai 0.
      - waktu            : lama memilih satu langkah, dalam milidetik.
    """

    def __init__(self):
        self.times_ms = []     # waktu tiap langkah
        self.nodes = []        # simpul diperiksa tiap langkah
        self.pruned = []       # cabang dipotong tiap langkah

    def record(self, elapsed_s, nodes, pruned):
        self.times_ms.append(elapsed_s * 1000)
        self.nodes.append(nodes)
        self.pruned.append(pruned)

    def reset(self):
        self.times_ms.clear()
        self.nodes.clear()
        self.pruned.clear()

    def summary(self):
        n = len(self.times_ms)
        if n == 0:
            return {"langkah": 0}
        return {
            "langkah": n,
            "waktu_total_ms": sum(self.times_ms),
            "waktu_rata2_ms": sum(self.times_ms) / n,
            "waktu_maks_ms": max(self.times_ms),
            "simpul_rata2": sum(self.nodes) / n,
            "simpul_maks": max(self.nodes),
            "simpul_total": sum(self.nodes),
            "dipotong_rata2": sum(self.pruned) / n,
            "dipotong_total": sum(self.pruned),
        }

    def __str__(self):
        s = self.summary()
        if s["langkah"] == 0:
            return "(belum ada data)"
        return (f"{s['langkah']} langkah | "
                f"waktu rata2 {s['waktu_rata2_ms']:.1f} ms, maks {s['waktu_maks_ms']:.1f} ms | "
                f"simpul rata2 {s['simpul_rata2']:.0f} | "
                f"dipotong rata2 {s['dipotong_rata2']:.0f}")


class _Counter:
    """Penghitung sementara untuk SATU kali pencarian."""
    __slots__ = ("nodes", "pruned")

    def __init__(self):
        self.nodes = 0
        self.pruned = 0


# ---------------------------------------------------------------------------
# Fungsi evaluasi
# ---------------------------------------------------------------------------
def evaluate(board, player):
    """Fungsi evaluasi dari sudut pandang `player`."""
    black, white = count_discs(board)
    opp = -player

    # Kondisi akhir permainan: hanya selisih disk yang penting
    if game_over(board):
        diff = (black - white) * player
        return 10000 * (1 if diff > 0 else -1 if diff < 0 else 0)

    # 1. Skor posisi (weighted matrix)
    positional = sum(WEIGHTS[r][c] * board[r][c] * player
                     for r in range(8) for c in range(8))

    # 2. Mobility: selisih jumlah langkah legal
    my_moves = len(get_valid_moves(board, player))
    opp_moves = len(get_valid_moves(board, opp))
    mobility = 5 * (my_moves - opp_moves)

    # 3. Selisih disk, bobotnya naik di akhir permainan
    total = black + white
    disc_diff = (black - white) * player
    disc_score = disc_diff * (total / 64) * 2

    return positional + mobility + disc_score


def _ordered_moves(board, current):
    """Langkah legal, kotak bernilai tinggi lebih dulu (dipakai kedua algoritma)."""
    moves = get_valid_moves(board, current)
    moves.sort(key=lambda m: WEIGHTS[m[0]][m[1]], reverse=True)
    return moves


# ---------------------------------------------------------------------------
# MiniMax murni (tanpa pruning)
# ---------------------------------------------------------------------------
def minimax(board, depth, current, ai, counter=None):
    """return (skor, langkah_terbaik)."""
    if counter is not None:
        counter.nodes += 1

    if depth == 0 or game_over(board):
        return evaluate(board, ai), None

    moves = _ordered_moves(board, current)

    if not moves:  # pass
        score, _ = minimax(board, depth - 1, -current, ai, counter)
        return score, None

    best_move = None
    if current == ai:  # MAX
        value = float('-inf')
        for move in moves:
            score, _ = minimax(apply_move(board, move, current), depth - 1,
                               -current, ai, counter)
            if score > value:
                value, best_move = score, move
    else:              # MIN
        value = float('inf')
        for move in moves:
            score, _ = minimax(apply_move(board, move, current), depth - 1,
                               -current, ai, counter)
            if score < value:
                value, best_move = score, move
    return value, best_move


# ---------------------------------------------------------------------------
# MiniMax + Alpha-Beta Pruning
# ---------------------------------------------------------------------------
def alphabeta(board, depth, alpha, beta, current, ai, counter=None):
    """
    current : pemain yang sedang giliran (BLACK / WHITE)
    ai      : pemain yang dimaksimalkan skornya
    return  : (skor, langkah_terbaik)
    """
    if counter is not None:
        counter.nodes += 1

    if depth == 0 or game_over(board):
        return evaluate(board, ai), None

    moves = _ordered_moves(board, current)

    # Pass: pemain tidak punya langkah, giliran pindah ke lawan
    if not moves:
        score, _ = alphabeta(board, depth - 1, alpha, beta, -current, ai, counter)
        return score, None

    best_move = None
    if current == ai:  # MAX
        value = float('-inf')
        for i, move in enumerate(moves):
            score, _ = alphabeta(apply_move(board, move, current), depth - 1,
                                 alpha, beta, -current, ai, counter)
            if score > value:
                value, best_move = score, move
            alpha = max(alpha, value)
            if alpha >= beta:
                if counter is not None:
                    counter.pruned += len(moves) - i - 1  # cabang yang dilewati
                break
        return value, best_move
    else:              # MIN
        value = float('inf')
        for i, move in enumerate(moves):
            score, _ = alphabeta(apply_move(board, move, current), depth - 1,
                                 alpha, beta, -current, ai, counter)
            if score < value:
                value, best_move = score, move
            beta = min(beta, value)
            if alpha >= beta:
                if counter is not None:
                    counter.pruned += len(moves) - i - 1
                break
        return value, best_move


# ---------------------------------------------------------------------------
# Greedy (algoritma pembanding, tanpa lookahead)
# ---------------------------------------------------------------------------
def greedy(board, player, counter=None):
    """
    Memilih langkah yang memberi jumlah disk terbanyak sekarang juga
    (= langkah yang membalik disk lawan paling banyak). Tidak memikirkan
    balasan lawan, tidak memakai WEIGHTS/mobility, dan tidak mengenal depth.
    return : (skor, langkah_terbaik)
    """
    if counter is not None:
        counter.nodes += 1                    # simpul akar

    moves = get_valid_moves(board, player)
    if not moves:
        return evaluate(board, player), None

    best_move, best_score = None, float('-inf')
    for move in moves:
        child = apply_move(board, move, player)
        if counter is not None:
            counter.nodes += 1                # satu simpul per langkah kandidat
        black, white = count_discs(child)
        score = (black - white) * player      # selisih disk setelah langkah
        if score > best_score:                # seri -> langkah pertama yang ditemukan
            best_score, best_move = score, move
    return best_score, best_move


# ---------------------------------------------------------------------------
# Antarmuka untuk game loop dan pengujian
# ---------------------------------------------------------------------------
def ai_choose_move(board, player, depth, algo="alphabeta", stats=None):
    """
    Memilih langkah untuk `player`.
    algo  : "alphabeta" (default), "minimax", atau "greedy"
            (greedy tidak memakai `depth`)
    stats : objek SearchStats; bila diberikan, waktu/simpul/pruning dicatat.
    """
    counter = _Counter()
    start = time.perf_counter()
    if algo == "minimax":
        _, move = minimax(board, depth, player, player, counter)
    elif algo == "greedy":
        _, move = greedy(board, player, counter)
    else:
        _, move = alphabeta(board, depth, float('-inf'), float('inf'),
                            player, player, counter)
    elapsed = time.perf_counter() - start

    if stats is not None:
        stats.record(elapsed, counter.nodes, counter.pruned)
    return move