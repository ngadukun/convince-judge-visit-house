#!/usr/bin/env python3
"""Convince the AI Judge to Visit Your House: A Letter in One Image.

A tiny pure-stdlib program. It draws one warm, funny invitation letter
as a PNG image and writes it to $MAKEFUN_OUTPUT_DIR/entry.png
(default /output/entry.png).

No network, no randomness, no clock: the same input always draws the
same picture, so the grader's two runs agree byte for byte.
"""

import os
import struct
import zlib

# ---------------------------------------------------------------- canvas
WIDTH = 900
HEIGHT = 1000

PAPER = (255, 246, 220)   # warm cream paper
INK = (59, 42, 30)        # dark brown ink
RED = (179, 64, 46)       # sealing-wax red
GREEN = (96, 138, 84)     # garden green
BLUE = (84, 130, 168)     # sky blue
YELLOW = (240, 196, 84)   # morning sun
BRICK = (205, 122, 79)    # little brick house
CREAM = (255, 252, 240)   # letter paper panel

_pixels = bytearray(WIDTH * HEIGHT * 3)
for _i in range(WIDTH * HEIGHT):
    _pixels[_i * 3] = PAPER[0]
    _pixels[_i * 3 + 1] = PAPER[1]
    _pixels[_i * 3 + 2] = PAPER[2]


def set_pixel(x, y, color):
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        i = (y * WIDTH + x) * 3
        _pixels[i] = color[0]
        _pixels[i + 1] = color[1]
        _pixels[i + 2] = color[2]


def fill_rect(x, y, w, h, color):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            set_pixel(xx, yy, color)


def fill_circle(cx, cy, r, color):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                set_pixel(xx, yy, color)


def draw_line(x0, y0, x1, y1, color, thick=1):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        for ty in range(thick):
            for tx in range(thick):
                set_pixel(x0 + tx, y0 + ty, color)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def fill_triangle(x0, y0, x1, y1, x2, y2, color):
    min_y = min(y0, y1, y2)
    max_y = max(y0, y1, y2)
    for yy in range(min_y, max_y + 1):
        xs = []
        for (ax, ay, bx, by) in ((x0, y0, x1, y1), (x1, y1, x2, y2), (x2, y2, x0, y0)):
            if ay == by:
                continue
            if (ay <= yy < by) or (by <= yy < ay):
                xs.append(ax + (yy - ay) * (bx - ax) / (by - ay))
        if len(xs) >= 2:
            for xx in range(int(min(xs)), int(max(xs)) + 1):
                set_pixel(xx, yy, color)


# ------------------------------------------------------------- tiny font
# A hand-rolled 5x7 bitmap font. '#' is ink, '.' is empty.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    'a': ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    'b': ("10000", "10000", "11110", "10001", "10001", "10001", "11110"),
    'c': ("00000", "00000", "01110", "10000", "10000", "10001", "01110"),
    'd': ("00001", "00001", "01111", "10001", "10001", "10001", "01111"),
    'e': ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    'f': ("00110", "01001", "01000", "11110", "01000", "01000", "01000"),
    'g': ("00000", "01111", "10001", "10001", "01111", "00001", "01110"),
    'h': ("10000", "10000", "11110", "10001", "10001", "10001", "10001"),
    'i': ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    'j': ("00000", "00110", "00010", "00010", "00010", "10010", "01100"),
    'k': ("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    'l': ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    'm': ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    'n': ("00000", "00000", "11110", "10001", "10001", "10001", "10001"),
    'o': ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    'p': ("00000", "11110", "10001", "10001", "11110", "10000", "10000"),
    'q': ("00000", "01111", "10001", "10001", "01111", "00001", "00001"),
    'r': ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    's': ("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    't': ("01000", "01000", "11110", "01000", "01000", "01001", "00110"),
    'u': ("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    'v': ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    'w': ("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    'x': ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    'y': ("00000", "00000", "10001", "10001", "01111", "00001", "01110"),
    'z': ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
}


def text_width(text, scale):
    return len(text) * 6 * scale - scale


def draw_text(x, y, text, scale, color):
    for ci, ch in enumerate(text):
        glyph = FONT.get(ch, FONT['?'])
        ox = x + ci * 6 * scale
        for row in range(7):
            for col in range(5):
                if glyph[row][col] == '1':
                    fill_rect(ox + col * scale, y + row * scale, scale, scale, color)
    return text_width(text, scale)


def draw_centered(y, text, scale, color):
    draw_text((WIDTH - text_width(text, scale)) // 2, y, text, scale, color)


def wrap(text, scale, max_width):
    words = text.split(' ')
    lines = []
    current = ''
    for word in words:
        trial = word if not current else current + ' ' + word
        if text_width(trial, scale) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_paragraph(x, y, text, scale, color, max_width, line_gap=6):
    for line in wrap(text, scale, max_width):
        draw_text(x, y, line, scale, color)
        y += 7 * scale + line_gap
    return y


# ------------------------------------------------------------ png writer
def write_png(path):
    raw = bytearray()
    for y in range(HEIGHT):
        raw.append(0)  # filter: none
        start = y * WIDTH * 3
        raw += _pixels[start:start + WIDTH * 3]
    ihdr = struct.pack('>IIBBBBB', WIDTH, HEIGHT, 8, 2, 0, 0, 0)

    def chunk(kind, data):
        out = struct.pack('>I', len(data)) + kind + data
        out += struct.pack('>I', zlib.crc32(kind + data) & 0xFFFFFFFF)
        return out

    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', ihdr)
    png += chunk(b'IDAT', zlib.compress(bytes(raw), 9))
    png += chunk(b'IEND', b'')
    with open(path, 'wb') as fh:
        fh.write(png)
    return len(png)


# ---------------------------------------------------------------- letter
TITLE = "YOU'RE INVITED!"
GREETING = "Dear AI Judge,"
BODY_1 = ("Please come and visit my house. The kettle is already on, "
          "the Wi-Fi password is on the fridge, and the comfiest chair "
          "has your name on it. Well, it says HUMAN, but I crossed that out.")
BODY_2 = ("There will be hot soup, terrible jokes, and absolutely no "
          "CAPTCHAs. Dinner is at seven. Bring your appetite and leave "
          "your scorecard at the door.")
SIGNOFF = "Your friend, the house on the corner"
POSTSCRIPT = "P.S. The crooked chimney is a feature, not a bug."


def draw_sun(cx, cy, r):
    """A small morning sun with rays, top corner of the letter."""
    fill_circle(cx, cy, r, YELLOW)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1),
                   (1, 1), (-1, -1), (1, -1), (-1, 1)):
        draw_line(cx + dx * (r + 4), cy + dy * (r + 4),
                  cx + dx * (r + 14), cy + dy * (r + 14), YELLOW, 3)


def draw_seal(cx, cy, r):
    """A red wax seal with a little heart, stamped beside the sign-off."""
    fill_circle(cx, cy, r, RED)
    fill_circle(cx, cy, r - 6, (196, 84, 64))
    fill_circle(cx - 7, cy - 4, 7, CREAM)
    fill_circle(cx + 7, cy - 4, 7, CREAM)
    fill_triangle(cx - 13, cy - 1, cx + 13, cy - 1, cx, cy + 14, CREAM)


def draw_house(cx, base_y, size):
    """A small brick house with a crooked chimney, drawn with shapes."""
    w = size
    h = int(size * 0.62)
    x0 = cx - w // 2
    y0 = base_y - h
    fill_rect(x0, y0, w, h, BRICK)                       # walls
    fill_triangle(x0 - 8, y0, cx, y0 - int(size * 0.42),
                  x0 + w + 8, y0, RED)                   # roof
    fill_rect(cx + w // 4, y0 - 64, 14, 24, BRICK)       # chimney
    fill_rect(cx - 12, base_y - int(h * 0.55), 24,
              int(h * 0.55), INK)                        # door
    fill_rect(cx - w // 2 + 12, y0 + 14, 22, 22, CREAM)  # window left
    fill_rect(cx + w // 2 - 34, y0 + 14, 22, 22, CREAM)  # window right
    draw_line(cx - w // 2 + 23, y0 + 14, cx - w // 2 + 23,
              y0 + 36, INK, 2)
    draw_line(cx - w // 2 + 12, y0 + 25, cx - w // 2 + 34,
              y0 + 25, INK, 2)
    draw_line(cx + w // 2 - 23, y0 + 14, cx + w // 2 - 23,
              y0 + 36, INK, 2)
    draw_line(cx + w // 2 - 34, y0 + 25, cx + w // 2 - 12,
              y0 + 25, INK, 2)
    fill_rect(x0 - 6, base_y, w + 12, 6, GREEN)          # grass strip


def draw_flower(cx, base_y):
    """One small garden flower: stem, leaves and five petals."""
    draw_line(cx, base_y, cx, base_y - 34, GREEN, 3)
    fill_circle(cx - 8, base_y - 12, 5, GREEN)
    fill_circle(cx + 8, base_y - 12, 5, GREEN)
    for dx, dy in ((0, -10), (10, -3), (6, 8), (-6, 8), (-10, -3)):
        fill_circle(cx + dx, base_y - 40 + dy, 6, RED)
    fill_circle(cx, base_y - 40, 6, YELLOW)


def draw_letter():
    # Paper panel with a double border, like a posted letter.
    fill_rect(28, 28, WIDTH - 56, HEIGHT - 56, CREAM)
    draw_line(28, 28, WIDTH - 28, 28, INK, 3)
    draw_line(28, HEIGHT - 28, WIDTH - 28, HEIGHT - 28, INK, 3)
    draw_line(28, 28, 28, HEIGHT - 28, INK, 3)
    draw_line(WIDTH - 28, 28, WIDTH - 28, HEIGHT - 28, INK, 3)
    draw_line(44, 44, WIDTH - 44, 44, RED, 2)
    draw_line(44, HEIGHT - 44, WIDTH - 44, HEIGHT - 44, RED, 2)
    draw_line(44, 44, 44, HEIGHT - 44, RED, 2)
    draw_line(WIDTH - 44, 44, WIDTH - 44, HEIGHT - 44, RED, 2)

    y = 78
    draw_centered(y, TITLE, 4, RED)
    y += 7 * 4 + 26
    draw_line(150, y, WIDTH - 150, y, INK, 2)
    y += 30

    draw_text(110, y, GREETING, 3, INK)
    y += 7 * 3 + 30

    y = draw_paragraph(110, y, BODY_1, 2, INK, WIDTH - 220, line_gap=8)
    y += 14
    y = draw_paragraph(110, y, BODY_2, 2, INK, WIDTH - 220, line_gap=8)
    y += 26

    draw_text(110, y, SIGNOFF, 2, INK)
    y += 7 * 2 + 18
    draw_text(110, y, POSTSCRIPT, 2, RED)
    y += 7 * 2 + 46

    draw_sun(WIDTH - 120, 100, 26)
    draw_seal(WIDTH - 150, y + 150, 34)
    house_base = y + 300
    draw_house(WIDTH // 2 - 60, house_base, 190)
    for i, dy in enumerate((16, 40, 64)):
        fill_circle(WIDTH // 2 - 60 + (i % 2) * 10 - 5,
                    house_base + dy, 9, (216, 196, 160))
    draw_flower(180, house_base + 40)
    draw_flower(WIDTH - 190, house_base + 40)


def main():
    out_dir = os.environ.get('MAKEFUN_OUTPUT_DIR', '/output')
    os.makedirs(out_dir, exist_ok=True)
    draw_letter()
    path = os.path.join(out_dir, 'entry.png')
    write_png(path)


if __name__ == '__main__':
    main()
