"""好きの種のアイコンを生成する。

図案は「声に出した瞬間」。押す白い丸と、そこから広がる二重の波紋。
アプリの中で実際に起きることと同じ形にしてある。

依存なしで動く（標準ライブラリのみ）。4倍のスーパーサンプリングで縁をなめらかにする。

    python3 tools/make-icons.py
"""

import math
import os
import struct
import zlib

# 呼び出したディレクトリに関係なく、リポジトリ直下へ書き出す
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# iOS Safari はホーム画面のアイコンを「URLごと」に長期キャッシュする。
# 絵を変えたらこの数字を上げ、参照側（shell-head.html / manifest.json / sw.js）も
# 揃えて書き換えること。同じファイル名のままでは端末に古い絵が残り続ける。
VERSION = 2
BG = (8, 8, 10)        # --void
FG = (250, 250, 247)   # --lume
SS = 4                 # 1辺あたりのサブサンプル数

# 半径・線幅・濃さはすべて画像サイズに対する比で持つ（どのサイズでも同じ見え方になる）
DOT_R = 0.150
RINGS = [
    (0.262, 0.016, 0.58),   # 半径, 線幅, 濃さ（外へ行くほど細く淡く＝広がって消える）
    (0.378, 0.010, 0.22),
]


def coverage(x, y, n):
    """その1点が白でどれだけ覆われるか（0.0〜1.0）を返す。"""
    c = (n - 1) / 2.0
    d = math.hypot(x - c, y - c) / n
    if d <= DOT_R:
        return 1.0
    for r, w, op in RINGS:
        if abs(d - r) <= w / 2.0:
            return op
    return 0.0


def render(n):
    rows = []
    step = 1.0 / SS
    off = step / 2.0
    for py in range(n):
        row = bytearray()
        for px in range(n):
            a = 0.0
            for sy in range(SS):
                for sx in range(SS):
                    a += coverage(px + off + sx * step, py + off + sy * step, n)
            a /= SS * SS
            row.extend(int(round(BG[i] + (FG[i] - BG[i]) * a)) for i in range(3))
        rows.append(row)
    return rows


def write_png(n, path):
    raw = bytearray()
    for row in render(n):
        raw.append(0)      # フィルタなし
        raw.extend(row)

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", n, n, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
           + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    print("%s  %dx%d  %d bytes" % (path, n, n, len(png)))


if __name__ == "__main__":
    for size in (180, 192, 512):
        write_png(size, "%s/icon-%d-v%d.png" % (OUT, size, VERSION))
