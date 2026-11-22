#!/usr/bin/env python3
"""World News, Saturday 21 November 2026 -- one image.

A hand-written renderer: it draws a newspaper front page that sums up
the six most consequential world stories of Saturday 21 November 2026.

    1. Iran strikes US positions in Bahrain (the Iran-US war)
    2. Russian missiles crash in Poland during a huge strike on Ukraine
    3. The World Court rules Myanmar committed the Rohingya genocide
    4. Trump and Xi hold talks at the APEC summit in Shenzhen
    5. COP31 climate talks in Antalya deadlock over fossil fuels
    6. Mexico captures the FBI most-wanted cartel boss "El Chapo Isidro"

Pure Python standard library. No network, no files read, no randomness:
running it twice writes byte-identical PNGs. Output is 1024x1024, well
under the 1 MiB limit.
"""

import binascii
import os
import struct
import zlib
from math import cos, radians, sin, sqrt

W = 1024
H = 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 242, 231)      # warm newspaper cream
PANEL = (255, 253, 247)      # panel white
INK = (18, 22, 30)           # near-black text
NAVY = (18, 40, 75)          # header band
NAVY_DARK = (10, 26, 52)
GOLD = (201, 162, 39)
RED = (178, 34, 34)
DARKRED = (120, 20, 20)
GREY = (110, 112, 118)
LIGHTGREY = (200, 200, 196)
SKY = (140, 180, 215)
SKY_DARK = (60, 90, 140)
SEA = (28, 80, 110)
SEA_DARK = (16, 52, 78)
ORANGE = (235, 120, 30)
AMBER = (245, 180, 60)
YELLOW = (250, 220, 90)
GREEN = (70, 130, 70)
HILL = (90, 150, 80)
BROWN = (120, 85, 50)
DESERT = (225, 170, 90)
SUNSET = (235, 130, 60)


# ---------------------------------------------------------------- canvas
class Canvas:
    """An RGB canvas backed by one flat bytearray."""

    def __init__(self, w, h, fill):
        self.w = w
        self.h = h
        self.buf = bytearray(bytes(fill) * (w * h))
        self.cx0, self.cy0, self.cx1, self.cy1 = 0, 0, w, h

    def set_clip(self, x, y, w, h):
        """Restrict all drawing to a rectangle (scenes stay in their box)."""
        self.cx0, self.cy0 = max(0, x), max(0, y)
        self.cx1, self.cy1 = min(self.w, x + w), min(self.h, y + h)

    def reset_clip(self):
        self.cx0, self.cy0, self.cx1, self.cy1 = 0, 0, self.w, self.h

    def px(self, x, y, c):
        if self.cx0 <= x < self.cx1 and self.cy0 <= y < self.cy1:
            i = (y * self.w + x) * 3
            self.buf[i] = c[0]
            self.buf[i + 1] = c[1]
            self.buf[i + 2] = c[2]

    def rect(self, x, y, w, h, c):
        """Fill a rectangle, clipped to the canvas and the clip box."""
        x0 = max(self.cx0, x)
        y0 = max(self.cy0, y)
        x1 = min(self.cx1, x + w)
        y1 = min(self.cy1, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(c) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.buf[i:i + len(row)] = row

    def hline(self, x, y, w, c):
        self.rect(x, y, w, 1, c)

    def vline(self, x, y, h, c):
        self.rect(x, y, 1, h, c)

    def line(self, x0, y0, x1, y1, c):
        """Bresenham line."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.px(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, c):
        """Filled circle via horizontal spans."""
        for dy in range(-r, r + 1):
            dx = int(sqrt(r * r - dy * dy))
            self.rect(cx - dx, cy + dy, 2 * dx + 1, 1, c)

    def ring(self, cx, cy, r, c, thick=2):
        for dy in range(-r, r + 1):
            dx = int(sqrt(r * r - dy * dy))
            for t in range(thick):
                rr = r - t
                if rr < 0:
                    break
                ddx = int(sqrt(rr * rr - dy * dy)) if rr >= abs(dy) else 0
                self.px(cx - ddx, cy + dy, c)
                self.px(cx + ddx, cy + dy, c)

    def poly(self, pts, c):
        """Fill a polygon with a scanline fill."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        y0, y1 = max(0, min(ys)), min(self.h - 1, max(ys))
        n = len(pts)
        for y in range(y0, y1 + 1):
            xs = []
            for i in range(n):
                x_a, y_a = pts[i]
                x_b, y_b = pts[(i + 1) % n]
                if y_a == y_b:
                    continue
                if (y_a <= y < y_b) or (y_b <= y < y_a):
                    t = (y - y_a) / (y_b - y_a)
                    xs.append(x_a + t * (x_b - x_a))
            if len(xs) >= 2:
                xs.sort()
                self.rect(int(xs[0]), y, int(xs[-1]) - int(xs[0]) + 1, 1, c)

    def vgrad(self, x, y, w, h, top, bottom):
        """Vertical gradient, top colour to bottom colour."""
        for i in range(h):
            t = i / max(1, h - 1)
            c = (int(top[0] + (bottom[0] - top[0]) * t),
                 int(top[1] + (bottom[1] - top[1]) * t),
                 int(top[2] + (bottom[2] - top[2]) * t))
            self.rect(x, y + i, w, 1, c)


def lerp(a, b, t):
    return (int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t))


# ---------------------------------------------------------------- PNG out
def write_png(cv, path):
    """Encode the canvas as a deterministic PNG (filter 0 rows)."""
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.buf[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 6)

    def chunk(kind, data):
        out = struct.pack(">I", len(data)) + kind + data
        out += struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", comp) + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# ---------------------------------------------------------------- font
# A hand-drawn 5x7 pixel font. '#' is a set pixel. Every glyph is written
# out here by hand; the renderer draws them scaled, with 1 unit of space
# between letters. Text is rendered in capitals.
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".....", "..#.."),
    ",": (".....", ".....", ".....", ".....", ".....", "..#..", "..#.."),
    ":": (".....", "..#..", ".....", ".....", ".....", "..#..", "....."),
    ";": (".....", "..#..", ".....", ".....", ".....", "..#..", "..#.."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "'": ("..#..", "..#..", ".....", ".....", ".....", ".....", "....."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "&": (".##..", "#..#.", "#..#.", ".#...", "#.#.#", "#..#.", ".##.#"),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "#": (".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."),
}

BLANK = (".....", ".....", ".....", ".....", ".....", ".....", ".....")


def text_w(s, scale):
    """Pixel width of a string at a scale (5 px glyph + 1 px gap)."""
    return len(s) * 6 * scale - scale if s else 0


def draw_text(cv, x, y, s, scale, color):
    """Draw one line of text, capitals, left aligned at (x, y)."""
    s = s.upper()
    cx = x
    for ch in s:
        glyph = FONT.get(ch, BLANK)
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == "#":
                    cv.rect(cx + col * scale, y + row * scale,
                            scale, scale, color)
        cx += 6 * scale


def draw_centred(cv, cx, y, s, scale, color):
    draw_text(cv, cx - text_w(s, scale) // 2, y, s, scale, color)


def wrap(s, max_px, scale):
    """Greedy word wrap into lines that fit max_px at the scale."""
    words = s.upper().split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_w(trial, scale) <= max_px or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- scenes
# Each scene draws inside the rectangle (x, y, w, h). All shapes are
# primitives: rectangles, lines, discs, triangles, gradients.

def scene_bahrain(cv, x, y, w, h):
    """Night over the Gulf: missile trails, fire over a base, the sea."""
    cv.vgrad(x, y, w, h, (8, 18, 42), (24, 48, 84))
    # stars
    for sx, sy in ((18, 14), (52, 30), (96, 10), (150, 26), (205, 12),
                   (250, 34), (300, 16), (340, 30), (390, 12), (440, 28),
                   (480, 14), (520, 32), (560, 16), (600, 30), (120, 44),
                   (230, 46), (360, 44), (500, 46)):
        if sx < w - 4 and sy < h - 60:
            cv.rect(x + sx, y + sy, 2, 2, (220, 225, 235))
    # moon
    cv.disc(x + w - 70, y + 34, 16, (235, 232, 205))
    cv.disc(x + w - 76, y + 30, 13, (8, 18, 42))
    # missile trails: two bright arcs crossing the sky
    cv.line(x + 40, y + h - 96, x + 300, y + 60, AMBER)
    cv.line(x + 42, y + h - 94, x + 302, y + 62, YELLOW)
    cv.line(x + 620, y + h - 110, x + 420, y + 70, AMBER)
    cv.line(x + 618, y + h - 108, x + 418, y + 72, YELLOW)
    cv.disc(x + 300, y + 60, 5, YELLOW)
    cv.disc(x + 420, y + 70, 5, YELLOW)
    # base buildings on the shore
    shore = y + h - 78
    cv.rect(x, shore, w, h - (shore - y), (12, 20, 34))
    for bx, bw, bh in ((30, 70, 46), (120, 46, 62), (185, 80, 38),
                       (290, 52, 58), (360, 90, 42), (470, 48, 52),
                       (540, 70, 36)):
        cv.rect(x + bx, shore - bh, bw, bh, (24, 34, 54))
        for wy in range(shore - bh + 8, shore - 8, 12):
            for wx in range(bx + 8, bx + bw - 8, 14):
                cv.rect(x + wx, wy, 4, 5, (250, 210, 110))
    # explosion glow over the second building
    ex, ey = x + 210, shore - 66
    cv.disc(ex, ey, 46, (200, 70, 20))
    cv.disc(ex, ey, 32, ORANGE)
    cv.disc(ex, ey, 18, AMBER)
    cv.disc(ex, ey, 9, YELLOW)
    # smoke puffs
    for sx, sy, sr in ((176, shore - 96, 12), (196, shore - 110, 15),
                       (222, shore - 104, 11), (244, shore - 118, 13)):
        cv.disc(x + sx, sy, sr, (70, 72, 80))
    # sea at the bottom with wave lines
    cv.rect(x, y + h - 22, w, 22, SEA)
    for wx in range(14, w - 10, 46):
        cv.line(x + wx, y + h - 12, x + wx + 22, y + h - 12, (90, 160, 200))
        cv.line(x + wx + 8, y + h - 6, x + wx + 30, y + h - 6, (70, 140, 180))


def scene_poland(cv, x, y, w, h):
    """A border under a grey sky: a Polish flag, fence, incoming missile."""
    cv.vgrad(x, y, w, h, (168, 186, 205), (214, 220, 226))
    gy = y + h - 18
    # low hills behind the ground band
    cv.disc(x + 50, gy + 34, 52, (150, 165, 150))
    cv.disc(x + w - 40, gy + 40, 62, (140, 158, 142))
    # ground
    cv.rect(x, gy, w, 18, (120, 128, 105))
    # flag pole with the Polish flag (white over red)
    fx = x + 20
    cv.vline(fx, y + 8, gy - y - 8, INK)
    cv.rect(fx + 2, y + 10, 36, 9, (250, 250, 250))
    cv.rect(fx + 2, y + 19, 36, 9, RED)
    # border fence posts and wire
    for px in range(x + 78, x + w - 16, 28):
        cv.vline(px, gy - 14, 14, (60, 60, 60))
    cv.line(x + 78, gy - 12, x + w - 16, gy - 12, (80, 80, 80))
    cv.line(x + 78, gy - 6, x + w - 16, gy - 6, (80, 80, 80))
    # one missile diving in, with flame
    cv.line(x + w - 34, y + 6, x + w - 96, y + 46, (70, 70, 78))
    cv.line(x + w - 32, y + 8, x + w - 94, y + 48, (110, 110, 118))
    cv.poly(((x + w - 96, y + 46), (x + w - 86, y + 38),
             (x + w - 104, y + 36)), INK)
    cv.disc(x + w - 32, y + 4, 5, ORANGE)
    cv.disc(x + w - 32, y + 4, 2, YELLOW)
    # warning triangle
    tx, ty = x + w - 52, gy - 46
    cv.poly(((tx, ty), (tx + 24, ty + 40), (tx - 24, ty + 40)),
            (245, 200, 40))
    cv.poly(((tx, ty + 6), (tx + 19, ty + 36), (tx - 19, ty + 36)), INK)
    cv.poly(((tx, ty + 10), (tx + 15, ty + 32), (tx - 15, ty + 32)),
            (245, 200, 40))
    cv.rect(tx - 2, ty + 15, 4, 12, INK)
    cv.rect(tx - 2, ty + 30, 4, 4, INK)


def scene_icj(cv, x, y, w, h):
    """The World Court: pediment, columns, the scales of justice."""
    cv.rect(x, y, w, h, (232, 226, 210))
    # pediment
    cv.poly(((x + 16, y + 26), (x + w // 2, y + 4), (x + w - 16, y + 26)),
            (196, 188, 168))
    cv.poly(((x + 30, y + 23), (x + w // 2, y + 10), (x + w - 30, y + 23)),
            (214, 206, 188))
    cv.disc(x + w // 2, y + 16, 4, GOLD)
    # columns, leaving the centre gap for the scales
    for cx in (x + 24, x + 88, x + 216, x + 280):
        cv.rect(cx, y + 30, 18, 40, (248, 244, 232))
        cv.rect(cx - 3, y + 27, 24, 5, (248, 244, 232))
        cv.rect(cx - 3, y + 68, 24, 5, (248, 244, 232))
        cv.vline(cx + 8, y + 33, 34, (210, 202, 184))
    # steps
    cv.rect(x + 20, y + 74, w - 40, 5, (200, 192, 172))
    cv.rect(x + 10, y + 79, w - 20, 5, (188, 180, 160))
    cv.rect(x, y + 84, w, 8, (176, 168, 148))
    # scales of justice in the centre gap
    sx = x + w // 2
    cv.vline(sx, y + 36, 26, GOLD)
    cv.disc(sx, y + 33, 3, GOLD)
    cv.line(sx - 26, y + 40, sx + 26, y + 40, GOLD)
    cv.line(sx - 26, y + 40, sx - 36, y + 54, GOLD)
    cv.line(sx - 26, y + 40, sx - 16, y + 54, GOLD)
    cv.line(sx + 26, y + 40, sx + 36, y + 54, GOLD)
    cv.line(sx + 26, y + 40, sx + 16, y + 54, GOLD)
    cv.poly(((sx - 40, y + 54), (sx - 12, y + 54), (sx - 26, y + 64)), GOLD)
    cv.poly(((sx + 40, y + 54), (sx + 12, y + 54), (sx + 26, y + 64)), GOLD)


def scene_apec(cv, x, y, w, h):
    """Shenzhen skyline at dusk with the US and Chinese flags."""
    cv.vgrad(x, y, w, h, (250, 190, 110), (200, 90, 70))
    cv.disc(x + w - 52, y + 34, 20, (255, 236, 170))
    # skyline
    base = y + h - 30
    cv.rect(x, base, w, 30, (40, 32, 48))
    for bx, bw, bh in ((8, 34, 90), (50, 26, 130), (84, 40, 70),
                       (132, 30, 150), (170, 44, 95), (222, 28, 120),
                       (258, 36, 80)):
        if bx + bw > w:
            break
        cv.rect(x + bx, base - bh, bw, bh, (52, 44, 62))
        for wy in range(base - bh + 10, base - 8, 16):
            for wx in range(bx + 6, bx + bw - 6, 12):
                cv.rect(x + wx, wy, 4, 5, (255, 210, 110))
    # two flag poles in front
    for fx, flag in ((x + 108, "us"), (x + 186, "cn")):
        cv.vline(fx, y + 96, base - y - 96, INK)
        if flag == "us":
            for s in range(7):
                cv.rect(fx + 2, y + 98 + s * 7, 58, 7,
                        RED if s % 2 == 0 else (250, 250, 250))
            cv.rect(fx + 2, y + 98, 26, 21, (40, 60, 130))
            for dx in (5, 13, 21):
                for dy in (4, 12):
                    cv.rect(fx + 2 + dx, y + 98 + dy, 3, 3, (250, 250, 250))
        else:
            cv.rect(fx + 2, y + 98, 58, 49, (200, 30, 30))
            cv.disc(fx + 14, y + 110, 5, YELLOW)
            for sx, sy in ((30, 104), (38, 112), (38, 122), (30, 130)):
                cv.disc(fx + sx, y + sy, 2, YELLOW)


def scene_cop31(cv, x, y, w, h):
    """Antalya: sun, wind turbines on green hills, a smoking stack."""
    cv.vgrad(x, y, w, h, (150, 200, 235), (235, 225, 190))
    cv.disc(x + 52, y + 36, 22, (255, 214, 90))
    for ang in range(0, 360, 45):
        rx = int(34 * cos(radians(ang)))
        ry = int(34 * sin(radians(ang)))
        cv.line(x + 52, y + 36, x + 52 + rx, y + 36 + ry, (255, 214, 90))
    # hills (low caps at the bottom of the scene)
    cv.disc(x + 30, y + h + 70, 120, HILL)
    cv.disc(x + w - 10, y + h + 80, 130, (70, 130, 70))
    # wind turbines standing on the hills
    for tx in (x + 70, x + 130, x + 196):
        ty = y + h - 50
        cv.vline(tx, ty - 62, 62, (245, 245, 245))
        cv.disc(tx, ty - 62, 4, (245, 245, 245))
        for ang in (90, 210, 330):
            ex = tx + int(22 * cos(radians(ang)))
            ey = ty - 62 + int(22 * sin(radians(ang)))
            cv.line(tx, ty - 62, ex, ey, (245, 245, 245))
    # smokestack with smoke, right side
    sx = x + w - 52
    cv.poly(((sx, y + h - 50), (sx + 22, y + h - 50),
             (sx + 18, y + h - 118), (sx + 4, y + h - 118)), (120, 110, 105))
    cv.rect(sx + 2, y + h - 122, 18, 5, (90, 82, 78))
    for px, py, pr in ((sx + 12, y + h - 132, 9), (sx + 22, y + h - 142, 12),
                       (sx + 34, y + h - 152, 10), (sx + 44, y + h - 164, 13)):
        cv.disc(px, py, pr, (150, 148, 145))


def scene_mexico(cv, x, y, w, h):
    """Desert sunset in Sinaloa: mountains, a road, police lights."""
    cv.vgrad(x, y, w, h, (250, 170, 80), (190, 70, 50))
    cv.disc(x + w - 60, y + 40, 24, (255, 230, 160))
    # mountains
    cv.poly(((x, y + h - 96), (x + 90, y + h - 190), (x + 180, y + h - 96)),
            (120, 70, 55))
    cv.poly(((x + 130, y + h - 96), (x + 240, y + h - 176),
             (x + w, y + h - 96)), (100, 58, 46))
    # desert floor
    cv.rect(x, y + h - 96, w, 96, (200, 140, 70))
    # road with perspective
    cv.poly(((x + w // 2 - 14, y + h - 96), (x + w // 2 + 14, y + h - 96),
             (x + w - 30, y + h), (x + 30, y + h)), (50, 48, 52))
    for i in range(4):
        t = i / 4
        cy = int(y + h - 96 + (96 * t))
        cw = int(3 + 6 * t)
        cv.rect(x + w // 2 - cw // 2, cy, cw, 5, (240, 220, 140))
    # police car silhouette on the road
    cx, cy = x + w // 2, y + h - 34
    cv.rect(cx - 52, cy - 18, 104, 18, (24, 26, 32))
    cv.poly(((cx - 34, cy - 18), (cx - 24, cy - 32), (cx + 24, cy - 32),
             (cx + 34, cy - 18)), (24, 26, 32))
    cv.rect(cx - 30, cy - 30, 20, 12, (150, 200, 235))
    cv.rect(cx + 10, cy - 30, 20, 12, (150, 200, 235))
    cv.disc(cx - 46, cy, 8, (20, 20, 22))
    cv.disc(cx + 46, cy, 8, (20, 20, 22))
    # flashing lights
    cv.disc(cx - 8, cy - 34, 12, (230, 40, 40))
    cv.disc(cx - 8, cy - 34, 6, (255, 120, 120))
    cv.disc(cx + 8, cy - 34, 12, (40, 90, 235))
    cv.disc(cx + 8, cy - 34, 6, (130, 180, 255))
    # cactus
    cv.vline(x + 34, y + h - 78, 40, GREEN)
    cv.line(x + 34, y + h - 62, x + 20, y + h - 62, GREEN)
    cv.vline(x + 20, y + h - 62, 12, GREEN)
    cv.line(x + 34, y + h - 52, x + 48, y + h - 52, GREEN)
    cv.vline(x + 48, y + h - 52, 12, GREEN)


# ---------------------------------------------------------------- panels
def panel(cv, x, y, w, h):
    cv.rect(x, y, w, h, PANEL)
    cv.rect(x, y, w, 2, INK)
    cv.rect(x, y + h - 2, w, 2, INK)
    cv.rect(x, y, 2, h, INK)
    cv.rect(x + w - 2, y, 2, h, INK)


def story_text(cv, x, y, w, headline, caption, hscale=2, cscale=2):
    """Headline lines then caption lines inside a panel text zone."""
    cy = y
    for line in headline:
        draw_text(cv, x, cy, line, hscale, INK)
        cy += 7 * hscale + 4
    cy += 2
    for line in caption:
        draw_text(cv, x, cy, line, cscale, (70, 70, 74))
        cy += 7 * cscale + 3
    return cy


# ---------------------------------------------------------------- compose
def compose():
    cv = Canvas(W, H, PAPER)

    # header band
    cv.rect(0, 0, W, 100, NAVY)
    cv.rect(0, 100, W, 4, GOLD)
    draw_centred(cv, W // 2, 14, "WORLD NEWS", 6, (250, 248, 240))
    draw_centred(cv, W // 2, 66, "SATURDAY 21 NOVEMBER 2026", 3, GOLD)

    # ---- lead story: Iran strikes US positions in Bahrain
    panel(cv, 12, 116, 652, 396)
    cv.set_clip(14, 118, 648, 240)
    scene_bahrain(cv, 14, 118, 648, 240)
    cv.reset_clip()
    draw_text(cv, 28, 368, "LEAD STORY - THE GULF WAR", 2, RED)
    draw_text(cv, 28, 390, "IRAN STRIKES US BASES", 3, INK)
    draw_text(cv, 28, 415, "IN BAHRAIN", 3, INK)
    cy = 448
    for line in wrap("IRGC says it hit US positions at two bases; "
                     "Bahrain reports a fire, no one hurt", 620, 2):
        draw_text(cv, 28, cy, line, 2, (70, 70, 74))
        cy += 17

    # ---- right column, top: Russian missiles crash in Poland
    panel(cv, 676, 116, 336, 192)
    cv.set_clip(678, 118, 332, 92)
    scene_poland(cv, 678, 118, 332, 92)
    cv.reset_clip()
    story_text(cv, 688, 218, 312,
               ["RUSSIAN MISSILES", "CRASH IN POLAND"],
               ["NATO: A GRAVE VIOLATION", "OF POLISH AIRSPACE"])

    # ---- right column, bottom: World Court rules on Myanmar
    panel(cv, 676, 320, 336, 192)
    cv.set_clip(678, 322, 332, 92)
    scene_icj(cv, 678, 322, 332, 92)
    cv.reset_clip()
    story_text(cv, 688, 422, 312,
               ["COURT: MYANMAR", "GUILTY OF GENOCIDE"],
               ["WORLD COURT RULES ON", "THE ROHINGYA"])

    # ---- bottom row, three stories
    # APEC: Trump and Xi in Shenzhen
    panel(cv, 12, 524, 325, 428)
    cv.set_clip(14, 526, 321, 274)
    scene_apec(cv, 14, 526, 321, 274)
    cv.reset_clip()
    story_text(cv, 26, 812, 309,
               ["TRUMP AND XI TALK", "AT APEC IN SHENZHEN"],
               ["LEADERS MEET IN CHINA;", "AGREE HUMAN OVERSIGHT",
                "OF MILITARY AI"])
    # COP31: climate talks in Antalya
    panel(cv, 349, 524, 326, 428)
    cv.set_clip(351, 526, 322, 274)
    scene_cop31(cv, 351, 526, 322, 274)
    cv.reset_clip()
    story_text(cv, 363, 812, 309,
               ["COP31 TALKS DEADLOCK", "OVER FOSSIL FUELS"],
               ["NATIONS SPLIT OVER", "PHASING OUT FOSSIL FUELS"])
    # Mexico: cartel boss captured
    panel(cv, 687, 524, 325, 428)
    cv.set_clip(689, 526, 321, 274)
    scene_mexico(cv, 689, 526, 321, 274)
    cv.reset_clip()
    story_text(cv, 701, 812, 309,
               ["MEXICO CAPTURES", "MOST-WANTED CARTEL BOSS"],
               ["FBI MOST-WANTED BOSS", "SEIZED IN A SINALOA RAID"])

    # footer
    cv.rect(0, 960, W, 2, GOLD)
    draw_centred(cv, W // 2, 976, "SIX STORIES THAT DEFINED THE DAY", 2, INK)

    return cv


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    size = write_png(compose(), path)
    print("wrote %s (%d bytes, %dx%d)" % (path, size, W, H))


if __name__ == "__main__":
    main()



