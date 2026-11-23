"""benchmark.py - Mengukur waktu, simpul, dan cabang dipotong (Skenario 2 dan 3)."""

import random

from board import BLACK, apply_move, game_over, get_valid_moves, new_board
from ai import SearchStats, ai_choose_move


def random_positions(n, seed=1):
    """n posisi dari game acak, tersebar dari awal sampai akhir permainan."""
    rng = random.Random(seed)
    positions = []
    while len(positions) < n:
        board, turn = new_board(), BLACK
        target = rng.randint(4, 54)          # kedalaman game acak
        for _ in range(target):
            if game_over(board):
                break
            moves = get_valid_moves(board, turn)
            if moves:
                board = apply_move(board, rng.choice(moves), turn)
            turn = -turn
        if not game_over(board) and get_valid_moves(board, turn):
            positions.append((board, turn))
    return positions


def compare(depths=(2, 3, 4), n_positions=30, seed=1):
    """MiniMax vs Alpha-Beta pada posisi yang sama."""
    positions = random_positions(n_positions, seed)
    print(f"{'Depth':<6}{'Algoritma':<12}{'Waktu rata2 (ms)':>18}{'Waktu maks (ms)':>17}"
          f"{'Simpul rata2':>14}{'Dipotong rata2':>16}")
    for d in depths:
        results = {}
        for algo in ("minimax", "alphabeta"):
            st = SearchStats()
            moves = []
            for board, turn in positions:
                moves.append(ai_choose_move(board, turn, d, algo, st))
            s = st.summary()
            results[algo] = (s, moves)
            print(f"{d:<6}{algo:<12}{s['waktu_rata2_ms']:>18.1f}{s['waktu_maks_ms']:>17.1f}"
                  f"{s['simpul_rata2']:>14.0f}{s['dipotong_rata2']:>16.0f}")
        mm, ab = results["minimax"][0], results["alphabeta"][0]
        same = sum(a == b for a, b in zip(results["minimax"][1], results["alphabeta"][1]))
        print(f"      -> pemotongan simpul {100 * (1 - ab['simpul_rata2'] / mm['simpul_rata2']):.1f}%, "
              f"percepatan waktu {mm['waktu_rata2_ms'] / ab['waktu_rata2_ms']:.1f}x, "
              f"langkah sama {same}/{len(positions)}")


if __name__ == "__main__":
    compare()
