"""report.py - Tabel hasil: skor, waktu, level, waktu rata-rata, simpul, cabang dipotong.

Dipakai oleh main.py (tampilan pygame + terminal) dan bisa dipakai ulang
oleh arena AI vs AI nanti.
"""

LEVEL_LABEL = {1: "Mudah", 3: "Sedang", 4: "Sulit"}
ALGO_LABEL = {"alphabeta": "Alpha-Beta", "minimax": "MiniMax", "greedy": "Greedy"}

# (judul kolom, kunci pada baris)
COLUMNS = [
    ("Pemain", "nama"),
    ("Skor", "skor"),
    ("Waktu", "waktu"),
    ("Level", "level"),
    ("Rata2 (ms)", "rata2_ms"),
    ("Simpul", "simpul"),
    ("Dipotong", "dipotong"),
]


def make_row(nama, skor, waktu_s, level, stats=None):
    """
    Membuat satu baris tabel (semua nilai sudah berupa teks).

    waktu_s : total waktu berpikir pemain selama game (detik)
    stats   : SearchStats milik AI. Untuk pemain manusia isi None,
              kolom rata2/simpul/dipotong akan berisi "-".
    """
    row = {
        "nama": nama,
        "skor": str(skor),
        "waktu": f"{waktu_s:.2f} s",
        "level": LEVEL_LABEL.get(level, str(level)),
        "rata2_ms": "-",
        "simpul": "-",
        "dipotong": "-",
    }
    if stats is not None and stats.summary()["langkah"] > 0:
        s = stats.summary()
        row["rata2_ms"] = f"{s['waktu_rata2_ms']:.1f}"
        row["simpul"] = str(s["simpul_total"])
        row["dipotong"] = str(s["dipotong_total"])
    return row


def format_table(rows):
    """Tabel teks rata kolom untuk dicetak di terminal."""
    headers = [h for h, _ in COLUMNS]
    keys = [k for _, k in COLUMNS]
    widths = [max(len(h), *(len(r[k]) for r in rows)) for h, k in COLUMNS]

    def line(cells):
        return " | ".join(c.ljust(w) for c, w in zip(cells, widths))

    sep = "-+-".join("-" * w for w in widths)
    out = [line(headers), sep]
    out += [line([r[k] for k in keys]) for r in rows]
    return "\n".join(out)