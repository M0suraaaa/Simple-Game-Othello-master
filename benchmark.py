"""main.py - Tampilan pygame dan game loop. Jalankan file ini."""

import time

import pygame

from board import (BLACK, WHITE, apply_move, count_discs, game_over,
                   get_valid_moves, new_board)
from ai import SearchStats, ai_choose_move
from report import ALGO_LABEL, COLUMNS, LEVEL_LABEL, format_table, make_row

CELL = 80
BOARD_SIZE = CELL * 8
BAR_HEIGHT = 70
WIDTH, HEIGHT = BOARD_SIZE, BOARD_SIZE + BAR_HEIGHT

GREEN = (34, 139, 34)
DARK_GREEN = (0, 90, 0)
BLACK_C = (20, 20, 20)
WHITE_C = (240, 240, 240)
HINT = (200, 200, 60)
BAR_BG = (40, 40, 40)

HUMAN, AI = BLACK, WHITE
AI_ALGO = "alphabeta"        # "alphabeta", "minimax", atau "greedy" (pembanding)

# Lebar kolom tabel di layar (piksel), urutan sesuai report.COLUMNS
COL_WIDTHS = [140, 45, 75, 70, 90, 80, 80]


def build_rows(board, depth, human_time_s, stats):
    """Dua baris tabel: pemain manusia dan AI."""
    black, white = count_discs(board)
    return [
        make_row("Kamu (Manusia)", black, human_time_s, depth),
        make_row(f"AI ({ALGO_LABEL[AI_ALGO]})", white,
                 stats.summary().get("waktu_total_ms", 0) / 1000, depth, stats),
    ]


def draw_table(screen, font, rows):
    """Tabel hasil sebagai panel di tengah papan."""
    row_h = 30
    panel_w = sum(COL_WIDTHS) + 20
    panel_h = row_h * (len(rows) + 2) + 20
    x0 = (WIDTH - panel_w) // 2
    y0 = (BOARD_SIZE - panel_h) // 2

    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    panel.fill((20, 20, 20, 225))
    screen.blit(panel, (x0, y0))
    pygame.draw.rect(screen, HINT, (x0, y0, panel_w, panel_h), 2)

    keys = [k for _, k in COLUMNS]
    # Judul kolom
    x = x0 + 10
    for (title, _), w in zip(COLUMNS, COL_WIDTHS):
        screen.blit(font.render(title, True, HINT), (x, y0 + 10))
        x += w
    pygame.draw.line(screen, HINT, (x0 + 10, y0 + 10 + row_h - 4),
                     (x0 + panel_w - 10, y0 + 10 + row_h - 4), 1)
    # Isi baris
    for i, row in enumerate(rows):
        x = x0 + 10
        y = y0 + 10 + row_h * (i + 1) + 4
        for key, w in zip(keys, COL_WIDTHS):
            screen.blit(font.render(row[key], True, WHITE_C), (x, y))
            x += w
    note = "T = sembunyikan tabel"
    screen.blit(font.render(note, True, (150, 150, 150)),
                (x0 + 10, y0 + panel_h - 24))


def draw_board(screen, font, board, valid_moves, turn, depth, message, over):
    screen.fill(GREEN)

    # Garis grid
    for i in range(9):
        pygame.draw.line(screen, DARK_GREEN, (i * CELL, 0), (i * CELL, BOARD_SIZE), 2)
        pygame.draw.line(screen, DARK_GREEN, (0, i * CELL), (BOARD_SIZE, i * CELL), 2)

    # Disk
    for r in range(8):
        for c in range(8):
            center = (c * CELL + CELL // 2, r * CELL + CELL // 2)
            if board[r][c] == BLACK:
                pygame.draw.circle(screen, BLACK_C, center, CELL // 2 - 8)
            elif board[r][c] == WHITE:
                pygame.draw.circle(screen, WHITE_C, center, CELL // 2 - 8)

    # Petunjuk langkah legal untuk pemain
    if not over and turn == HUMAN:
        for r, c in valid_moves:
            center = (c * CELL + CELL // 2, r * CELL + CELL // 2)
            pygame.draw.circle(screen, HINT, center, 8)

    # Bar informasi
    pygame.draw.rect(screen, BAR_BG, (0, BOARD_SIZE, WIDTH, BAR_HEIGHT))
    black, white = count_discs(board)
    score_text = (f"Kamu (Hitam): {black}   AI (Putih): {white}   "
                  f"Level: {LEVEL_LABEL.get(depth, depth)}")
    screen.blit(font.render(score_text, True, WHITE_C), (10, BOARD_SIZE + 8))

    if over:
        if black > white:
            status = "Game selesai: Kamu menang! (R = main lagi)"
        elif white > black:
            status = "Game selesai: AI menang! (R = main lagi)"
        else:
            status = "Game selesai: Seri! (R = main lagi)"
    elif message:
        status = message
    else:
        status = "Giliranmu (T = tabel)" if turn == HUMAN else "AI sedang berpikir..."
    screen.blit(font.render(status, True, HINT), (10, BOARD_SIZE + 38))


def main(depth=3):
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Othello - MiniMax + Alpha-Beta")
    font = pygame.font.SysFont(None, 28)
    table_font = pygame.font.SysFont(None, 22)
    clock = pygame.time.Clock()

    def reset_game():
        return new_board(), HUMAN, "", SearchStats(), 0.0, None, False, False

    # board, turn, message, stats, waktu manusia, mulai berpikir, tabel?, sudah dicetak?
    (board, turn, message, stats,
     human_time, think_start, show_table, printed) = reset_game()
    running = True

    while running:
        over = game_over(board)
        valid_moves = get_valid_moves(board, turn) if not over else []

        # Pass otomatis jika pemain yang giliran tidak punya langkah
        if not over and not valid_moves:
            who = "Kamu" if turn == HUMAN else "AI"
            message = f"{who} tidak punya langkah, giliran dilewati"
            turn = -turn
            valid_moves = get_valid_moves(board, turn)

        # Mulai menghitung waktu berpikir pemain manusia
        if turn == HUMAN and not over and valid_moves and think_start is None:
            think_start = time.perf_counter()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                new_level = None
                if event.key == pygame.K_r:
                    new_level = depth
                elif event.key == pygame.K_1:
                    new_level = 1
                elif event.key == pygame.K_2:
                    new_level = 3
                elif event.key == pygame.K_3:
                    new_level = 4
                elif event.key == pygame.K_t:
                    show_table = not show_table

                if new_level is not None:
                    # Ganti level atau restart = game baru, supaya data tabel konsisten
                    depth = new_level
                    (board, turn, message, stats,
                     human_time, think_start, show_table, printed) = reset_game()
            elif event.type == pygame.MOUSEBUTTONDOWN and turn == HUMAN and not over:
                x, y = event.pos
                if y < BOARD_SIZE:
                    r, c = y // CELL, x // CELL
                    if (r, c) in valid_moves:
                        if think_start is not None:
                            human_time += time.perf_counter() - think_start
                            think_start = None
                        board = apply_move(board, (r, c), HUMAN)
                        turn = AI
                        message = ""

        over = game_over(board)
        draw_board(screen, font, board, valid_moves, turn, depth, message, over)

        # Tabel: otomatis saat game selesai, atau kapan saja dengan tombol T
        if over or show_table:
            rows = build_rows(board, depth, human_time, stats)
            draw_table(screen, table_font, rows)
            if over and not printed:
                print(format_table(rows))
                printed = True
        pygame.display.flip()

        # Giliran AI (layar digambar dulu supaya terlihat "berpikir")
        if turn == AI and not over and valid_moves:
            move = ai_choose_move(board, AI, depth, AI_ALGO, stats)
            if move:
                board = apply_move(board, move, AI)
            turn = HUMAN

        clock.tick(30)

    pygame.quit()


if __name__ == "__main__":
    main(depth=3)