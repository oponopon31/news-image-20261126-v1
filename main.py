#!/usr/bin/env python3
"""News26 v2 — THE WORLD IN ONE DAY top + Grand Obelisk body:
Thursday 26 November 2026.

A single-file program that draws one editorial front page (1024x1024 PNG)
summarising the verified world news of Thursday 26 November 2026.

Style: "THE WORLD IN ONE DAY" masthead (top bar + huge date +
terracotta sub-headline + 6-stat row) over a Grand Obelisk / World
Dispatch body — cream paper, dark teal bands, brick-red accents, flat
vector editorial illustrations (geometric shapes, no outlines). 3 large
lead cards + 9 smaller cards (illustration on the left), dark stats band,
Also list, large dark map, Day in UTC, Date Check.

Runs offline, no network. Draws the whole page at 2048x2048 and
LANCZOS-downsamples to 1024x1024. Writes entry.png to $MAKEFUN_OUTPUT_DIR
(or the current directory). Deterministic: the same bytes on every run.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- constants
SCALE = 2            # supersampling: draw at 2048, deliver at 1024
W = 1024 * SCALE
H = 1024 * SCALE
M = 16 * SCALE       # outer margin (v4, World Dispatch: near full-bleed)
CW = W - 2 * M       # content width (992 in 1024-space)

# muted editorial palette: dark navy / teal / terracotta / warm cream / mustard
PAPER = (250, 246, 236)
CARD = (253, 251, 246)
INK = (27, 42, 74)
NAVY = (34, 53, 92)
NAVY_DK = (20, 31, 56)
TEAL = (46, 125, 123)
TEAL_DK = (31, 94, 92)
DARK_TEAL = (22, 58, 68)   # World Dispatch dark band / map background
MAP_DK = (24, 58, 68)      # dark map background (v4 bottom row)
MAROON = (146, 44, 54)     # RUSSIA-UKRAINE region segment
TEAL_LT = (220, 233, 228)
TEAL_PALE = (191, 216, 210)
TERRA = (198, 93, 59)
TERRA_DK = (168, 74, 44)
RED = (172, 52, 40)       # Grand Obelisk brick red: locations, pins, times
TERRA_LT = (242, 220, 210)
MUSTARD = (217, 164, 65)
MUSTARD_DK = (186, 138, 44)
MUSTARD_LT = (246, 232, 200)
PURPLE = (110, 82, 120)
PLUM = (84, 58, 92)
GREEN = (96, 128, 84)
SAND = (239, 227, 200)
GREY = (74, 74, 69)
MUTED = (107, 107, 98)
RULE_LT = (229, 220, 200)
WHITE = (255, 255, 255)
SKY_DK = (58, 74, 102)
CLOUD = (96, 110, 138)

_FONTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")

# Real MS fonts bundled with the entry (user-uploaded Georgia + Arial),
# loaded via a path relative to __file__ so the grader finds them offline
# in /bot. System DejaVu / Liberation paths are kept only as a fallback.
SERIF_BOLD_PATHS = [
    os.path.join(_FONTS_DIR, "Georgia-Bold.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
]
SERIF_PATHS = [
    os.path.join(_FONTS_DIR, "Georgia-Regular.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
]
SERIF_ITALIC_PATHS = [
    os.path.join(_FONTS_DIR, "Georgia-Italic.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
]
SANS_BOLD_PATHS = [
    os.path.join(_FONTS_DIR, "Arial-Bold.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]
SANS_PATHS = [
    os.path.join(_FONTS_DIR, "Arial-Regular.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]


def _load_ttf(paths, size):
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return None


class FallbackFont:
    """Stand-in for a missing TTF: carries the intended size so the
    bitmap fallback can render text at the right scale."""

    def __init__(self, size):
        self.size = size
        self.is_fallback = True


class Fonts:
    """Georgia (serif) for masthead + big headlines; Arial (sans) for
    everything else. Loads the bundled MS fonts from fonts/ next to this
    file, so the page renders identically offline. Falls back to system
    DejaVu / Liberation, then to a FallbackFont carrying the intended size,
    so the page can still be drawn with Pillow's built-in bitmap font,
    upscaled.
    """

    def __init__(self):
        self._sb = {}
        self._sr = {}
        self._si = {}
        self._snb = {}
        self._snr = {}
        self.has_ttf = (
            _load_ttf(SERIF_BOLD_PATHS, 10) is not None
            or _load_ttf(SANS_PATHS, 10) is not None
        )
        self._default = ImageFont.load_default()

    def _get(self, cache, paths, size):
        if size not in cache:
            f = _load_ttf(paths, size)
            cache[size] = f if f is not None else FallbackFont(size)
        return cache[size]

    def serif_bold(self, size):
        return self._get(self._sb, SERIF_BOLD_PATHS, size)

    def serif_reg(self, size):
        return self._get(self._sr, SERIF_PATHS, size)

    def serif_italic(self, size):
        return self._get(self._si, SERIF_ITALIC_PATHS, size)

    def sans_bold(self, size):
        return self._get(self._snb, SANS_BOLD_PATHS, size)

    def sans_reg(self, size):
        return self._get(self._snr, SANS_PATHS, size)


F = Fonts()


def s(v):
    """Scale a 1024-space value to the 2048 drawing canvas."""
    return int(round(v * SCALE))


# ------------------------------------------------------------------- page
class Page:
    def __init__(self):
        self.img = Image.new("RGB", (W, H), PAPER)
        self.d = ImageDraw.Draw(self.img, "RGBA")

    # -- primitives ------------------------------------------------------
    def rect(self, x, y, w, h, fill, outline=None, width=1):
        self.d.rectangle([x, y, x + w, y + h], fill=fill, outline=outline,
                         width=width)

    def rrect(self, x, y, w, h, r, fill, outline=None, width=1):
        self.d.rounded_rectangle([x, y, x + w, y + h], radius=r, fill=fill,
                                 outline=outline, width=width)

    def ellipse(self, x, y, w, h, fill, outline=None, width=1):
        self.d.ellipse([x, y, x + w, y + h], fill=fill, outline=outline,
                       width=width)

    def poly(self, pts, fill, outline=None):
        self.d.polygon(pts, fill=fill, outline=outline)

    def line(self, pts, fill, width=1):
        self.d.line(pts, fill=fill, width=width)

    def arc(self, box, a0, a1, fill, width=1):
        self.d.arc(box, a0, a1, fill=fill, width=width)

    # -- text ------------------------------------------------------------
    def _ttf_text(self, x, y, text, font, fill, anchor):
        self.d.text((x, y), text, font=font, fill=fill, anchor=anchor)

    def _fallback_text(self, x, y, text, size, fill, anchor):
        """Render with the built-in bitmap font, upscaled to `size`."""
        base = self._default
        tmp = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
        td = ImageDraw.Draw(tmp)
        bb = td.textbbox((0, 0), text, font=base)
        w0, h0 = bb[2] - bb[0], bb[3] - bb[1]
        if w0 <= 0 or h0 <= 0:
            return
        pad = 2
        img = Image.new("RGBA", (w0 + 2 * pad, h0 + 2 * pad), (0, 0, 0, 0))
        idd = ImageDraw.Draw(img)
        idd.text((pad - bb[0], pad - bb[1]), text, font=base,
                 fill=fill + (255,))
        scale = size / float(max(h0, 1))
        nw = max(1, int(round(img.width * scale)))
        nh = max(1, int(round(img.height * scale)))
        img = img.resize((nw, nh), Image.LANCZOS)
        # anchor handling: "la" = left/top, "ma" = centre/top, "ra" = right/top
        if anchor == "ma":
            x -= nw // 2
        elif anchor == "ra":
            x -= nw
        self.img.paste(img, (int(x), int(y)), img)

    def text(self, x, y, text, font, fill, anchor="la"):
        """Draw one line of text. `font` is a PIL font or a FallbackFont."""
        if getattr(font, "is_fallback", False):
            self._fallback_text(x, y, text, font.size, fill, anchor)
        else:
            self._ttf_text(x, y, text, font, fill, anchor)

    def text_w(self, text, font):
        if getattr(font, "is_fallback", False):
            return len(text) * font.size * 0.58
        return self.d.textlength(text, font=font)

    def wrap(self, text, font, max_w):
        """Greedy word wrap; returns a list of lines that fit max_w."""
        words = text.split()
        if not words:
            return [""]
        lines, cur = [], words[0]
        for w in words[1:]:
            trial = cur + " " + w
            if self.text_w(trial, font) <= max_w:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
        return lines

    def para(self, x, y, text, font, fill, max_w, max_lines, lh):
        """Draw a wrapped paragraph, at most max_lines lines; ellipsis if cut.

        Returns the y just below the last drawn line.
        """
        lines = self.wrap(text, font, max_w)
        shown = lines[:max_lines]
        if len(lines) > max_lines and shown:
            last = shown[-1]
            while last and self.text_w(last + " ...", font) > max_w:
                last = last[:-1].rstrip()
            shown[-1] = last + " ..."
        for i, ln in enumerate(shown):
            self.text(x, y + i * lh, ln, font, fill)
        return y + len(shown) * lh

    def tracked(self, x, y, text, font, fill, tracking, anchor="la"):
        """Draw text with extra letter spacing (for small-caps bars)."""
        widths = [self.text_w(ch, font) for ch in text]
        total = sum(widths) + tracking * max(len(text) - 1, 0)
        if anchor == "ma":
            x -= total // 2
        elif anchor == "ra":
            x -= total
        cx = x
        for ch, w in zip(text, widths):
            self.text(cx, y, ch, font, fill)
            cx += w + tracking
        return cx

    def fit(self, text, font_fn, size, max_w, min_size=10):
        """Shrink a font until `text` fits max_w; returns (font, size)."""
        while size > min_size:
            f = font_fn(size)
            if self.text_w(text, f) <= max_w:
                return f, size
            size -= 1
        return font_fn(min_size), min_size


# ---------------------------------------------------------------- helpers
def chip(pg, x, y, num, bg, fg, size=17):
    """Numbered story chip: a small filled square with a number.

    `size` is the 1024-space font size; the square is 26 (1024-space)."""
    sq = s(26)
    fs = s(size)
    pg.rrect(x, y, sq, sq, s(4), bg)
    f = F.sans_bold(fs)
    tw = pg.text_w(num, f)
    pg.text(x + (sq - tw) // 2, y + (sq - fs) // 2 + s(1), num, f, fg)


def tag(pg, x, y, label, bg, fg=WHITE, size=15):
    """Small filled status/location tag; returns width used.

    `size` is the 1024-space font size; the tag is 24 tall (1024-space)."""
    fs = s(size)
    f = F.sans_bold(fs)
    tw = pg.text_w(label, f)
    pad = s(8)
    h = s(24)
    pg.rrect(x, y, tw + 2 * pad, h, s(4), bg)
    pg.text(x + pad, y + (h - fs) // 2 + s(1), label, f, fg)
    return tw + 2 * pad


def tag_sm(pg, x, y, label, bg, fg=WHITE, size=10):
    """Compact status tag for the v4 cards (18 tall in 1024-space).

    Returns the width used."""
    fs = s(size)
    f = F.sans_bold(fs)
    tw = pg.text_w(label, f)
    pad = s(6)
    h = s(18)
    pg.rrect(x, y, tw + 2 * pad, h, s(3), bg)
    pg.text(x + pad, y + (h - fs) // 2 + s(1), label, f, fg)
    return tw + 2 * pad


def _clip_draw(pg, draw_fn, x, y, w, h):
    """Draw an illustration clipped to its panel.

    Renders onto a temp image of the panel size, then pastes it. This
    prevents illustration elements that overshoot the panel (e.g. the 6G
    signal arcs, storm clouds, tanker waves) from spilling into the text
    area of the card.
    """
    tmp = Image.new("RGB", (w, h), CARD)
    sub = Page.__new__(Page)
    sub.img = tmp
    sub.d = ImageDraw.Draw(tmp, "RGBA")
    draw_fn(sub, 0, 0, w, h)
    pg.img.paste(tmp, (x, y))

# ------------------------------------------------------- lead illustrations
def draw_kuwait(pg, x, y, w, h):
    """Air-defence surveillance site: radar dish, tower, drone, blast puffs."""
    pg.rect(x, y, w, h, SAND)
    # sky band
    pg.rect(x, y, w, int(h * 0.62), (240, 232, 205))
    # low sun
    pg.ellipse(x + int(w * 0.78), y + int(h * 0.10), s(46), s(46), MUSTARD)
    # drone: dark quadcopter upper right
    cx, cy = x + int(w * 0.66), y + int(h * 0.22)
    pg.poly([(cx, cy - s(10)), (cx + s(12), cy), (cx, cy + s(10)),
             (cx - s(12), cy)], INK)
    for dx, dy in ((-16, -12), (16, -12), (-16, 12), (16, 12)):
        pg.ellipse(cx + s(dx) - s(5), cy + s(dy) - s(5), s(10), s(10), INK)
    pg.line([(cx - s(16), cy - s(12)), (cx + s(16), cy + s(12))], INK, s(3))
    pg.line([(cx + s(16), cy - s(12)), (cx - s(16), cy + s(12))], INK, s(3))
    # ground
    gy = y + int(h * 0.72)
    pg.rect(x, gy, w, h - int(h * 0.72), (214, 196, 160))
    # radar tower + dish, left of centre
    tx = x + int(w * 0.30)
    pg.rect(tx - s(14), gy - int(h * 0.34), s(28), int(h * 0.34), NAVY)
    pg.rect(tx - s(26), gy - int(h * 0.38), s(52), s(10), NAVY)
    # dish: half-ellipse in teal, tilted
    pg.ellipse(tx + s(6), gy - int(h * 0.52), s(74), s(56), TEAL)
    pg.poly([(tx + s(10), gy - int(h * 0.40)), (tx + s(76), gy - int(h * 0.44)),
             (tx + s(76), gy - int(h * 0.36)), (tx + s(10), gy - int(h * 0.34))],
            TEAL_DK)
    # small building block
    pg.rect(x + int(w * 0.58), gy - int(h * 0.16), s(90), int(h * 0.16), NAVY_DK)
    pg.rect(x + int(w * 0.58) + s(10), gy - int(h * 0.13), s(14), s(14),
            MUSTARD_LT)
    pg.rect(x + int(w * 0.58) + s(34), gy - int(h * 0.13), s(14), s(14),
            MUSTARD_LT)
    # blast puffs near the tower base (terracotta, flat circles)
    for dx, dy, r in ((0.16, 0.66, 16), (0.22, 0.70, 11), (0.12, 0.72, 9)):
        pg.ellipse(x + int(w * dx) - s(r), y + int(h * dy) - s(r),
                   s(2 * r), s(2 * r), TERRA)
    pg.ellipse(x + int(w * 0.19) - s(7), y + int(h * 0.62) - s(7),
               s(14), s(14), (232, 150, 110))


def draw_ebola(pg, x, y, w, h):
    """Bundibugyo virus particle on deep teal, with a medical cross badge.

    All sizes are fractions of the panel (w, h) so it fits any panel.
    """
    pg.rect(x, y, w, h, TEAL_DK)
    # virus: central body + radiating spikes, sized to the panel height
    cx, cy = x + w // 2, y + int(h * 0.52)
    r = int(h * 0.26)
    spike = int(h * 0.13)
    dot = max(2, int(h * 0.045))
    import math as _m
    for k in range(12):
        ang = _m.pi * 2 * k / 12
        x1 = cx + int(r * 0.95 * _m.cos(ang))
        y1 = cy + int(r * 0.95 * _m.sin(ang))
        x2 = cx + int((r + spike) * _m.cos(ang))
        y2 = cy + int((r + spike) * _m.sin(ang))
        pg.line([(x1, y1), (x2, y2)], MUSTARD, max(2, int(h * 0.035)))
        pg.ellipse(x2 - dot, y2 - dot, 2 * dot, 2 * dot, MUSTARD)
    pg.ellipse(cx - r, cy - r, 2 * r, 2 * r, MUSTARD)
    pg.ellipse(cx - int(r * 0.38), cy - int(r * 0.38), int(r * 0.76),
               int(r * 0.76), MUSTARD_DK)
    # small satellite viruses
    for dx, dy, rr in ((0.14, 0.18, 0.07), (0.84, 0.20, 0.05),
                       (0.86, 0.78, 0.06)):
        vx, vy = x + int(w * dx), y + int(h * dy)
        pr = int(h * rr)
        pg.ellipse(vx - pr, vy - pr, 2 * pr, 2 * pr, (217, 164, 65))
    # medical cross badge, bottom left (top left is taken by the number
    # badge — a cross there collides with it on the large lead card)
    bx, by = x + int(w * 0.025), y + int(h * 0.62)
    bs = int(h * 0.28)
    pg.rrect(bx, by, bs, bs, max(2, bs // 6), WHITE)
    pg.rect(bx + int(bs * 0.38), by + int(bs * 0.18), int(bs * 0.24),
            int(bs * 0.64), TERRA)
    pg.rect(bx + int(bs * 0.18), by + int(bs * 0.38), int(bs * 0.64),
            int(bs * 0.24), TERRA)


def draw_gaza(pg, x, y, w, h):
    """Dawn over a city skyline: mustard horizon, flat towers, smoke plume."""
    # sky bands: teal top, mustard horizon
    pg.rect(x, y, w, int(h * 0.55), (58, 96, 110))
    pg.rect(x, y + int(h * 0.55), w, int(h * 0.17), MUSTARD)
    pg.rect(x, y + int(h * 0.72), w, h - int(h * 0.72), (38, 48, 70))
    # rising sun
    pg.ellipse(x + int(w * 0.72), y + int(h * 0.30), s(56), s(56), (246, 220, 160))
    # skyline: flat towers of varied height
    base = y + h
    towers = [(0.00, 0.34, 0.10), (0.11, 0.44, 0.09), (0.21, 0.30, 0.12),
              (0.34, 0.50, 0.10), (0.45, 0.38, 0.11), (0.57, 0.55, 0.09),
              (0.67, 0.40, 0.12), (0.80, 0.48, 0.10), (0.91, 0.34, 0.09)]
    for fx, fh, fw in towers:
        tx = x + int(w * fx)
        tw = int(w * fw)
        th = int(h * fh)
        pg.rect(tx, base - th, tw, th, NAVY_DK)
        # lit windows
        for wy in range(2):
            pg.rect(tx + s(6), base - th + s(8) + wy * s(22), s(8), s(8),
                    MUSTARD_LT)
    # smoke plume from one tower (flat grey-terra circles, rising)
    sx = x + int(w * 0.60)
    for i, (dy, r) in enumerate(((0.30, 13), (0.22, 17), (0.13, 21))):
        pg.ellipse(sx - s(r) + i * s(4), y + int(h * dy) - s(r),
                   s(2 * r), s(2 * r), (120, 110, 105) if i < 2 else TERRA)
    # small birds
    for bx, by in ((0.18, 0.16), (0.30, 0.11)):
        px, py = x + int(w * bx), y + int(h * by)
        pg.arc([px - s(10), py - s(6), px + s(10), py + s(6)], 200, 340, INK,
               s(3))

# ----------------------------------------------------- feature illustrations
def _stars_circle(pg, cx, cy, r, n, col, dot):
    import math as _m
    for k in range(n):
        ang = _m.pi * 2 * k / n - _m.pi / 2
        px = cx + int(r * _m.cos(ang))
        py = cy + int(r * _m.sin(ang))
        pg.ellipse(px - dot, py - dot, 2 * dot, 2 * dot, col)


def draw_eu(pg, x, y, w, h):
    """EU budget summit: navy field, circle of stars, hemicycle seats."""
    pg.rect(x, y, w, h, NAVY)
    _stars_circle(pg, x + w // 2, y + int(h * 0.40), int(h * 0.30), 12,
                  MUSTARD, max(2, int(h * 0.05)))
    for rr, col in ((int(h * 0.52), MUSTARD_LT), (int(h * 0.38), TEAL_LT)):
        pg.arc([x + w // 2 - rr, y + int(h * 0.92) - rr,
                x + w // 2 + rr, y + int(h * 0.92) + rr], 180, 360, col,
               max(2, int(h * 0.06)))
    pg.rect(x, y + int(h * 0.92), w, h - int(h * 0.92), (20, 31, 56))


def draw_storm(pg, x, y, w, h):
    """Thanksgiving nor'easter: dark clouds, rain, a leaning power pole."""
    pg.rect(x, y, w, h, SKY_DK)
    for cx, cy, cw, ch in ((0.16, 0.18, 0.42, 0.34), (0.46, 0.10, 0.46, 0.36),
                           (0.70, 0.22, 0.40, 0.32)):
        pg.ellipse(x + int(w * cx), y + int(h * cy), int(w * cw),
                   int(h * ch), CLOUD)
    pg.ellipse(x + int(w * 0.30), y + int(h * 0.06), int(w * 0.34),
               int(h * 0.30), (116, 130, 156))
    for i in range(8):
        rx = x + int(w * (0.08 + 0.11 * i))
        ry = y + int(h * 0.56)
        pg.line([(rx, ry), (rx - max(2, int(h * 0.06)), ry + int(h * 0.26))],
                (190, 205, 215), max(2, int(h * 0.04)))
    px = x + int(w * 0.78)
    pg.line([(px, y + int(h * 0.55)), (px + int(h * 0.12), y + h)],
            (60, 48, 40), max(2, int(h * 0.08)))
    pg.line([(px - int(h * 0.22), y + int(h * 0.60)),
             (px + int(h * 0.26), y + int(h * 0.64))], (60, 48, 40),
            max(2, int(h * 0.06)))


def draw_zelensky(pg, x, y, w, h):
    """Podium + microphone + Ukrainian flag (blue over mustard)."""
    pg.rect(x, y, w, h, TEAL)
    fx = x + int(w * 0.10)
    pg.line([(fx, y + int(h * 0.10)), (fx, y + int(h * 0.88))],
            (240, 240, 235), max(2, int(h * 0.05)))
    fw = int(w * 0.26)
    pg.rect(fx, y + int(h * 0.12), fw, int(h * 0.24), (47, 105, 178))
    pg.rect(fx, y + int(h * 0.36), fw, int(h * 0.24), MUSTARD)
    px = x + int(w * 0.55)
    pg.poly([(px - int(w * 0.14), y + h), (px - int(w * 0.11), y + int(h * 0.55)),
             (px + int(w * 0.11), y + int(h * 0.55)),
             (px + int(w * 0.14), y + h)], NAVY_DK)
    pg.rect(px - int(w * 0.14), y + int(h * 0.50), int(w * 0.28),
            max(2, int(h * 0.08)), MUSTARD)
    pg.line([(px + int(w * 0.08), y + int(h * 0.50)),
             (px + int(w * 0.12), y + int(h * 0.30))], INK,
            max(2, int(h * 0.04)))
    pg.ellipse(px + int(w * 0.10), y + int(h * 0.22), max(3, int(h * 0.14)),
               max(3, int(h * 0.14)), INK)


def draw_migration(pg, x, y, w, h):
    """Falling bars + a big down arrow: net migration 77,000."""
    pg.rect(x, y, w, h, CARD)
    base = y + int(h * 0.84)
    pg.line([(x + int(w * 0.05), base), (x + int(w * 0.95), base)], INK,
            max(2, int(h * 0.04)))
    bars = [(0.12, 0.60, TEAL), (0.30, 0.48, TEAL), (0.48, 0.34, TEAL),
            (0.66, 0.22, TERRA)]
    bw = int(w * 0.12)
    for fx, fh, col in bars:
        bx = x + int(w * fx)
        bh = int(h * fh)
        pg.rect(bx, base - bh, bw, bh, col)
    ax = x + int(w * 0.86)
    pg.line([(ax, y + int(h * 0.10)), (ax, y + int(h * 0.58))], TERRA_DK,
            max(2, int(h * 0.08)))
    pg.poly([(ax - int(h * 0.14), y + int(h * 0.46)),
             (ax + int(h * 0.14), y + int(h * 0.46)),
             (ax, y + int(h * 0.66))], TERRA_DK)


def draw_refinery(pg, x, y, w, h):
    """Refinery towers with a flame and smoke."""
    pg.rect(x, y, w, h, SAND)
    pg.rect(x, y + int(h * 0.74), w, h - int(h * 0.74), (214, 196, 160))
    for fx, fw, fh in ((0.08, 0.16, 0.50), (0.28, 0.20, 0.60),
                       (0.52, 0.14, 0.42)):
        tx = x + int(w * fx)
        tw = int(w * fw)
        th = int(h * fh)
        top = y + h - th - int(h * 0.26)
        pg.rect(tx, top, tw, th, NAVY)
        for i in range(3):
            pg.rect(tx, top + i * int(h * 0.18), tw, max(2, int(h * 0.04)),
                    TEAL_LT)
    fx = x + int(w * 0.78)
    fy = y + int(h * 0.38)
    pg.poly([(fx, fy - int(h * 0.30)), (fx + int(h * 0.20), fy + int(h * 0.06)),
             (fx + int(h * 0.08), fy + int(h * 0.26)),
             (fx - int(h * 0.08), fy + int(h * 0.26)),
             (fx - int(h * 0.20), fy + int(h * 0.06))], TERRA)
    pg.poly([(fx, fy - int(h * 0.14)), (fx + int(h * 0.10), fy + int(h * 0.08)),
             (fx, fy + int(h * 0.20)), (fx - int(h * 0.10), fy + int(h * 0.08))],
            MUSTARD)
    for dx, dy, r in ((0.74, 0.16, 0.13), (0.84, 0.10, 0.10),
                      (0.66, 0.08, 0.08)):
        pr = int(h * r)
        pg.ellipse(x + int(w * dx) - pr, y + int(h * dy) - pr, 2 * pr, 2 * pr,
                   (150, 145, 138))


def draw_tanker(pg, x, y, w, h):
    """Capsized tanker on a teal sea, with a life ring."""
    pg.rect(x, y, w, h, (64, 120, 128))
    pg.rect(x, y, w, int(h * 0.30), (120, 165, 175))
    for wy in (0.42, 0.60, 0.78):
        pg.arc([x - int(w * 0.05), y + int(h * wy), x + int(w * 0.45),
                y + int(h * wy) + int(h * 0.30)], 200, 340,
               (210, 232, 230), max(2, int(h * 0.05)))
        pg.arc([x + int(w * 0.55), y + int(h * wy), x + w + int(w * 0.05),
                y + int(h * wy) + int(h * 0.30)], 200, 340,
               (210, 232, 230), max(2, int(h * 0.05)))
    hx, hy = x + int(w * 0.28), y + int(h * 0.52)
    pg.poly([(hx, hy), (hx + int(w * 0.42), hy - int(h * 0.16)),
             (hx + int(w * 0.46), hy + int(h * 0.24)),
             (hx + int(w * 0.02), hy + int(h * 0.28))], (30, 38, 54))
    pg.rect(hx + int(w * 0.10), hy - int(h * 0.28), int(w * 0.20),
            int(h * 0.12), (30, 38, 54))
    pg.rect(hx + int(w * 0.10), hy - int(h * 0.28), int(w * 0.20),
            max(2, int(h * 0.05)), TERRA)
    rx, ry = x + int(w * 0.82), y + int(h * 0.72)
    ro = int(h * 0.22)
    ri = int(h * 0.11)
    pg.ellipse(rx - ro, ry - ro, 2 * ro, 2 * ro, MUSTARD)
    pg.ellipse(rx - ri, ry - ri, 2 * ri, 2 * ri, (64, 120, 128))


def draw_6g(pg, x, y, w, h):
    """Satellite + signal arcs on a dark navy sky."""
    pg.rect(x, y, w, h, NAVY_DK)
    for dx, dy in ((0.08, 0.14), (0.20, 0.08), (0.88, 0.12), (0.94, 0.30),
                   (0.10, 0.70), (0.90, 0.72)):
        d = max(2, int(h * 0.06))
        pg.ellipse(x + int(w * dx), y + int(h * dy), d, d, WHITE)
    ax, ay = x + int(w * 0.82), y + int(h * 0.30)
    for r in (int(h * 0.24), int(h * 0.40), int(h * 0.56)):
        pg.arc([ax - r, ay - r, ax + r, ay + r], 300, 60, TEAL_LT,
               max(2, int(h * 0.05)))
    cx, cy = x + int(w * 0.42), y + int(h * 0.52)
    pw, ph = int(w * 0.14), int(h * 0.36)
    pg.rect(cx - pw - int(w * 0.05), cy - ph // 2, pw, ph, TEAL)
    pg.rect(cx + int(w * 0.05), cy - ph // 2, pw, ph, TEAL)
    bw, bh = int(w * 0.10), int(h * 0.60)
    pg.rect(cx - bw // 2, cy - bh // 2, bw, bh, MUSTARD)
    pg.ellipse(cx - int(h * 0.10), cy - int(h * 0.10), int(h * 0.20),
               int(h * 0.20), WHITE)
    pg.line([(cx, cy - bh // 2), (cx, cy - int(h * 0.52))], WHITE,
            max(2, int(h * 0.04)))
    pg.ellipse(cx - max(2, int(h * 0.05)), cy - int(h * 0.58),
               max(4, int(h * 0.10)), max(4, int(h * 0.10)), TERRA)


def draw_armenia(pg, x, y, w, h):
    """Mountains + a border fence with an open gate + tricolour flag."""
    pg.rect(x, y, w, h, SAND)
    pg.poly([(x, y + int(h * 0.74)), (x + int(w * 0.22), y + int(h * 0.32)),
             (x + int(w * 0.44), y + int(h * 0.74))], TEAL)
    pg.poly([(x + int(w * 0.30), y + int(h * 0.74)),
             (x + int(w * 0.55), y + int(h * 0.20)),
             (x + int(w * 0.80), y + int(h * 0.74))], TEAL_DK)
    pg.poly([(x + int(w * 0.50), y + int(h * 0.30)),
             (x + int(w * 0.55), y + int(h * 0.20)),
             (x + int(w * 0.60), y + int(h * 0.30))], WHITE)
    pg.rect(x, y + int(h * 0.74), w, h - int(h * 0.74), (214, 196, 160))
    fy = y + int(h * 0.60)
    for i in range(7):
        fx = 0.06 + 0.13 * i
        if 0.38 < fx < 0.56:
            continue  # gate opening
        pg.rect(x + int(w * fx), fy, max(2, int(h * 0.06)),
                int(h * 0.34), INK)
    pg.line([(x + int(w * 0.03), fy + int(h * 0.08)),
             (x + int(w * 0.97), fy + int(h * 0.08))], INK,
            max(2, int(h * 0.04)))
    pg.line([(x + int(w * 0.03), fy + int(h * 0.24)),
             (x + int(w * 0.97), fy + int(h * 0.24))], INK,
            max(2, int(h * 0.04)))
    fx = x + int(w * 0.82)
    pg.line([(fx, y + int(h * 0.10)), (fx, y + int(h * 0.54))], INK,
            max(2, int(h * 0.04)))
    for i, col in enumerate(((198, 60, 50), (40, 80, 160), (230, 140, 50))):
        pg.rect(fx, y + int(h * 0.12) + i * int(h * 0.13), int(w * 0.14),
                int(h * 0.13), col)


def draw_spacex(pg, x, y, w, h):
    """Rocket + falling debris over a beach."""
    pg.rect(x, y, w, h, (120, 165, 175))
    pg.rect(x, y + int(h * 0.76), w, h - int(h * 0.76), SAND)
    pg.arc([x - int(w * 0.05), y + int(h * 0.74), x + int(w * 0.5),
            y + int(h * 0.74) + int(h * 0.28)], 200, 340, WHITE,
           max(2, int(h * 0.04)))
    rx, ry = x + int(w * 0.42), y + int(h * 0.34)
    bw = int(w * 0.045)
    pg.poly([(rx, ry - int(h * 0.44)), (rx + bw, ry - int(h * 0.16)),
             (rx + bw, ry + int(h * 0.34)), (rx - bw, ry + int(h * 0.34)),
             (rx - bw, ry - int(h * 0.16))], (235, 235, 230))
    pg.poly([(rx - bw, ry + int(h * 0.34)), (rx - int(w * 0.08), ry + int(h * 0.52)),
             (rx - bw, ry + int(h * 0.44))], TERRA)
    pg.poly([(rx + bw, ry + int(h * 0.34)), (rx + int(w * 0.08), ry + int(h * 0.52)),
             (rx + bw, ry + int(h * 0.44))], TERRA)
    pg.ellipse(rx - int(h * 0.07), ry - int(h * 0.06), int(h * 0.14),
               int(h * 0.14), TEAL_DK)
    pg.poly([(rx - int(h * 0.08), ry + int(h * 0.52)),
             (rx + int(h * 0.08), ry + int(h * 0.52)),
             (rx, ry + int(h * 0.74))], MUSTARD)
    for dx, dy, dw, dh in ((0.70, 0.82, 0.06, 0.08), (0.82, 0.88, 0.045, 0.10),
                           (0.62, 0.90, 0.07, 0.07), (0.88, 0.80, 0.035, 0.12)):
        pg.rect(x + int(w * dx), y + int(h * dy), max(2, int(w * dw)),
                max(2, int(h * dh)), INK)


def draw_india_uae(pg, x, y, w, h):
    """Two flags (India + UAE) with a gear between them."""
    pg.rect(x, y, w, h, CARD)
    fx, fy = x + int(w * 0.06), y + int(h * 0.22)
    fw, fh = int(w * 0.30), int(h * 0.52)
    for i, col in enumerate(((255, 153, 51), WHITE, (19, 136, 8))):
        pg.rect(fx, fy + i * (fh // 3), fw, fh // 3, col)
    pg.ellipse(fx + fw // 2 - int(h * 0.09), fy + fh // 2 - int(h * 0.09),
               int(h * 0.18), int(h * 0.18), NAVY)
    gx = x + int(w * 0.62)
    pg.rect(gx, fy, int(w * 0.07), fh, (200, 16, 46))
    for i, col in enumerate(((0, 122, 61), WHITE, (0, 0, 0))):
        pg.rect(gx + int(w * 0.07), fy + i * (fh // 3), fw - int(w * 0.07),
                fh // 3, col)
    cx, cy = x + w // 2, y + int(h * 0.72)
    ro = int(h * 0.18)
    pg.ellipse(cx - ro, cy - ro, 2 * ro, 2 * ro, MUSTARD)
    pg.ellipse(cx - ro // 2, cy - ro // 2, ro, ro, CARD)
    import math as _m
    for k in range(8):
        ang = _m.pi * 2 * k / 8
        tx = cx + int(ro * 1.25 * _m.cos(ang))
        ty = cy + int(ro * 1.25 * _m.sin(ang))
        td = max(2, ro // 3)
        pg.ellipse(tx - td, ty - td, 2 * td, 2 * td, MUSTARD)

# ------------------------------------------------------------------- map
CONTINENTS = {
    "NA": [(-168, 66), (-150, 70), (-130, 71), (-110, 72), (-95, 80),
           (-80, 73), (-65, 62), (-55, 52), (-60, 45), (-70, 42),
           (-75, 35), (-81, 26), (-84, 30), (-90, 21), (-97, 16),
           (-105, 20), (-112, 24), (-117, 32), (-124, 40), (-124, 48),
           (-132, 58), (-150, 60), (-165, 60)],
    "SA": [(-78, 8), (-62, 10), (-52, 5), (-44, -3), (-35, -8),
           (-40, -20), (-48, -28), (-58, -38), (-66, -47), (-70, -54),
           (-73, -40), (-73, -25), (-77, -12), (-80, -4)],
    "EU": [(-10, 36), (0, 37), (10, 39), (20, 41), (28, 38), (30, 44),
           (24, 46), (18, 45), (12, 44), (6, 43), (0, 44), (-3, 48),
           (-8, 50), (-4, 56), (2, 58), (8, 60), (16, 63), (24, 68),
           (30, 70), (34, 66), (36, 58), (30, 52), (22, 50), (14, 52),
           (6, 54), (0, 50), (-6, 46), (-10, 40)],
    "AF": [(-17, 15), (-12, 25), (-6, 30), (0, 35), (10, 37), (20, 32),
           (30, 31), (33, 27), (37, 22), (40, 18), (43, 12), (48, 11),
           (51, 10), (46, 2), (41, -5), (40, -12), (36, -18), (33, -26),
           (28, -33), (20, -35), (16, -29), (13, -18), (12, -10),
           (9, -2), (9, 4), (4, 6), (-2, 5), (-8, 5), (-13, 8), (-16, 12)],
    "AS": [(30, 70), (40, 70), (50, 72), (60, 70), (70, 72), (80, 73),
           (90, 75), (100, 76), (110, 74), (120, 73), (130, 72),
           (140, 72), (150, 70), (160, 69), (170, 67), (178, 65),
           (180, 62), (170, 60), (162, 58), (158, 52), (150, 45),
           (142, 42), (140, 38), (135, 35), (130, 32), (127, 35),
           (122, 38), (120, 32), (118, 25), (110, 20), (108, 15),
           (105, 10), (100, 8), (98, 12), (95, 16), (92, 20), (88, 22),
           (85, 20), (80, 15), (77, 10), (75, 12), (72, 20), (68, 23),
           (65, 25), (62, 25), (58, 26), (55, 26), (52, 28), (50, 30),
           (48, 30), (45, 29), (42, 30), (40, 32), (38, 36), (36, 36),
           (34, 36), (32, 37), (30, 36)],
    "OC": [(113, -22), (118, -15), (124, -12), (130, -12), (136, -12),
           (142, -11), (146, -16), (150, -22), (153, -27), (152, -32),
           (150, -37), (145, -38), (140, -38), (135, -35), (130, -32),
           (125, -33), (120, -34), (115, -32), (113, -26)],
}

PINS = [("01", 54, 32), ("02", 23, -3), ("03", 30, 26), ("05", -77, 39),
        ("08", 100, 14), ("09", 0, 40), ("10", 118, 44),
        ("12", -97, 26), ("27", 110, 18)]


def draw_map(pg, x, y, w, h):
    """Flat world map (equirectangular) with numbered story pins."""
    pg.rect(x, y, w, h, TEAL_LT)
    # graticule: faint latitude lines
    for lat in (60, 30, 0, -30):
        gy = y + int((75 - lat) / 135.0 * h)
        pg.line([(x, gy), (x + w, gy)], (200, 218, 212), s(2))
    for lon, lat in [(-150, 0), (-60, 0), (30, 0), (120, 0)]:
        gx = x + int((lon + 180) / 360.0 * w)
        pg.line([(gx, y), (gx, y + h)], (200, 218, 212), s(2))
    for pts in CONTINENTS.values():
        proj = [(x + int((lo + 180) / 360.0 * w),
                 y + int((75 - la) / 135.0 * h)) for lo, la in pts]
        pg.poly(proj, TEAL_PALE)
    # pins
    for num, lon, lat in PINS:
        px = x + int((lon + 180) / 360.0 * w)
        py = y + int((75 - lat) / 135.0 * h)
        r = s(9)
        pg.ellipse(px - r, py - r, 2 * r, 2 * r, MUSTARD)
        pg.ellipse(px - r, py - r, 2 * r, 2 * r, None, INK, s(1))
        f = F.sans_bold(10)
        tw = pg.text_w(num, f)
        pg.text(px - tw // 2, py - s(5), num, f, INK)


# Pin coordinates for the 12 illustrated cards (lon, lat).
PINS_V4 = [("01", 48, 29), ("02", 23, -3), ("03", 34, 31),
           ("04", 4, 51), ("05", -74, 41), ("06", 30, 50),
           ("07", 0, 51), ("08", 100, 14), ("09", 1, 39),
           ("10", 116, 40), ("11", 44, 40), ("12", -97, 26)]

# Manual declutter offsets (1024-space dx, dy) for the dense Europe /
# Middle East pin cluster. Without these, London/Brussels (4 deg apart)
# and the Gaza/Kuwait/Yerevan triangle (each ~14-15 px apart) overlap:
# the pins are 15 px squares on a 1 px-per-degree map. After these
# offsets every pair of pin centres is >= 17 px apart.
PIN_OFFSETS = {"01": (6, 2), "03": (-4, 8), "04": (8, -4),
               "07": (-10, -2), "11": (2, -6)}


def draw_map_dark(pg, x, y, w, h):
    """Large dark-teal world map (v6, Grand Obelisk): pale continents,
    RED SQUARE numbered pins for the 12 illustrated cards."""
    pg.rect(x, y, w, h, MAP_DK)
    # graticule: faint latitude/longitude lines
    for lat in (60, 30, 0, -30):
        gy = y + int((75 - lat) / 135.0 * h)
        pg.line([(x, gy), (x + w, gy)], (44, 84, 94), s(1))
    for lon in (-150, -60, 30, 120):
        gx = x + int((lon + 180) / 360.0 * w)
        pg.line([(gx, y), (gx, y + h)], (44, 84, 94), s(1))
    for pts in CONTINENTS.values():
        proj = [(x + int((lo + 180) / 360.0 * w),
                 y + int((75 - la) / 135.0 * h)) for lo, la in pts]
        pg.poly(proj, (214, 204, 172))
    # pins: RED SQUARES with white numbers. The Europe / Middle East cluster
    # is dense — PIN_OFFSETS nudges the colliding pins apart (see above).
    # Two passes: all squares first, then all numbers on top, so a later
    # pin's square can never cover an earlier pin's number.
    f = F.sans_bold(8)
    pts = []
    for num, lon, lat in PINS_V4:
        px = x + int((lon + 180) / 360.0 * w)
        py = y + int((75 - lat) / 135.0 * h)
        dx, dy = PIN_OFFSETS.get(num, (0, 0))
        px += s(dx)
        py += s(dy)
        pts.append((num, px, py))
        sq = s(15)
        pg.rect(px - sq // 2, py - sq // 2, sq, sq, RED)
    for num, px, py in pts:
        tw = pg.text_w(num, f)
        pg.text(px - tw // 2, py - s(4), num, f, WHITE)
    # a few place labels (cream, small). Cream text with a dark halo so it
    # reads on both the dark sea and the pale land (Kuwait sits on land).
    # Labels follow the (possibly nudged) pin positions.
    f_lab = F.sans_reg(8)
    pin_xy = {num: (px, py) for num, px, py in pts}
    for label, num, dx, dy in (
            ("Kuwait", "01", 12, -4),
            ("New York", "05", 12, -4),
            ("Bangkok", "08", 12, -4)):
        px, py = pin_xy[num]
        lx = px + s(dx)
        ly = py + s(dy)
        for ox, oy in ((-s(1), 0), (s(1), 0), (0, -s(1)), (0, s(1))):
            pg.text(lx + ox, ly + oy, label, f_lab, DARK_TEAL)
        pg.text(lx, ly, label, f_lab, (232, 222, 190))


# ------------------------------------------------------------------- data
LEADS = [
    {"num": "01", "tag": "KUWAIT", "status": "CLAIM", "src": "Reuters / BBC",
     "head": "Two Italians killed in drone strike in Kuwait",
     "summ": "Two Italian technicians killed at a Skyguard station. Italy "
             "and Kuwait blame Iran.",
     "draw": draw_kuwait},
    {"num": "02", "tag": "DR CONGO", "status": "OFFICIAL",
     "src": "Reuters / AP",
     "head": "DR Congo Ebola passes 12,000 cases",
     "summ": "12,021 cases and 5,904 deaths. Bundibugyo virus; no approved "
             "vaccine.",
     "draw": draw_ebola},
    {"num": "03", "tag": "GAZA", "status": "OFFICIAL / CLAIM",
     "src": "Reuters",
     "head": "Israel kills Hamas official Abu Nada in Gaza",
     "summ": "Abu Nada and his wife killed in a dawn strike; 10 Palestinians "
             "killed in Gaza that day.",
     "draw": draw_gaza},
]

FEATURES = [
    ("04", "EU BUDGET", "EU budget summit ends in deadlock",
     "€1.78T compromise, €204bn cut; leaders split after ~14 hours.",
     "European Council", draw_eu),
    ("05", "USA", "Thanksgiving storm cuts power to ~1M",
     "961,000 without power; 2,200+ flights delayed; parade to Sat.",
     "BBC / Reuters", draw_storm),
    ("06", "UKRAINE", "Zelensky: US focus is on Middle East",
     "Patriot deliveries delayed; Trump–Putin ties 'very strange'.",
     "BBC", draw_zelensky),
    ("07", "UNITED KINGDOM", "UK net migration falls to 77,000",
     "Lowest since 1997, down 92% from the 944,000 peak.",
     "ONS / BBC", draw_migration),
    ("08", "THAILAND", "Bangkok refinery blast injures 9",
     "Blast at Bangchak plant; 3 in critical condition.",
     "AP", draw_refinery),
    ("09", "SPAIN", "Ibiza tanker capsizes; 1 dead, 17 rescued",
     "Med Emre carried up to 7,000 tonnes of diesel.",
     "Reuters / BBC", draw_tanker),
    ("10", "CHINA", "China unveils 6G roadmap to 2030",
     "Commercial 6G and LEO satellite internet by 2030.",
     "Xinhua", draw_6g),
    ("11", "ARMENIA", "Armenia to end Russian guards",
     "Russian guards in place since 1992 to hand over.",
     "Interfax", draw_armenia),
    ("12", "MEXICO", "Mexico seeks talks over SpaceX airspace",
     "Starship debris washed up at Playa Bagdad; 5.9 kg collected.",
     "Reuters", draw_spacex),
    ("13", "INDIA–UAE", "India–UAE fast-track defence kit",
     "14th joint committee meets in Abu Dhabi.",
     "Def Min", draw_india_uae),
]

# Card status tags (v4, World Dispatch single-word style).
CARD_STATUS = {
    "01": "CLAIM", "02": "OFFICIAL", "03": "OFFICIAL",
    "04": "REPORT", "05": "REPORT", "06": "CLAIM",
    "07": "OFFICIAL", "08": "REPORT", "09": "REPORT",
    "10": "OFFICIAL", "11": "OFFICIAL", "12": "REPORT",
}
# Status tag fill colours.
STATUS_BG = {"OFFICIAL": TEAL, "CLAIM": TERRA, "REPORT": NAVY}

# The 12 illustrated cards (v6, Grand Obelisk: 3 large leads on top,
# 9 smaller features below, illustration on the left):
# the 3 leads + 9 features. #13 India-UAE is moved to Also (least visual /
# routine committee story), so the Also list has 28 items (13-40).
CARDS = []
for _lead in LEADS:
    CARDS.append({"num": _lead["num"], "loc": _lead["tag"],
                  "status": CARD_STATUS[_lead["num"]],
                  "head": _lead["head"], "summ": _lead["summ"],
                  "src": _lead["src"], "draw": _lead["draw"]})
for _num, _region, _head, _summ, _src, _fn in FEATURES:
    if _num == "13":
        continue  # moved to Also
    CARDS.append({"num": _num, "loc": _region,
                  "status": CARD_STATUS[_num],
                  "head": _head, "summ": _summ, "src": _src, "draw": _fn})

# Stats band (v4, World Dispatch dark band): 4 verified full-day outcomes.
# Numbers are gold (MUSTARD) on the dark teal band; captions are white.
# "250 troops returned" is NOT in the verified set — replaced by 56 Europa goals.
STATS = [
    ("3.25%", "South Korea rate after 25 bps hike", MUSTARD),
    ("56", "goals in 18 Europa League games", MUSTARD),
    ("+12.2%", "Australia Q3 business investment", MUSTARD),
    ("~1M", "without power, Thanksgiving storm", MUSTARD),
]

# Top stats row (v8): the 6 numbers at the top, below the sub-headline,
# matching the reference top crop's layout (large number on top +
# caption below, evenly spaced across the width). VERIFIED numbers
# (v3 corrections), NOT the reference's unverified ones: no "60 MPH"
# stat — 60 mph is the midpoint of the verified 50–70 mph gust range
# (and it already appears in the sub-headline); no "2027" (the loan is
# verified, the year is not); no "on AI servers" (the capex is verified,
# the AI detail is not); no "250" (not in the verified set — replaced
# by the 56 Europa League goals). Order matches the reference positions.
TOP_STATS = [
    ("~1M", "without power, Thanksgiving storm"),
    ("€45BN", "proposed EU loan for Ukraine"),
    ("3.25%", "South Korea rate after 25 bps hike"),
    ("18 YRS", "since 26/11 Mumbai terror attacks"),
    ("+12.2%", "Australia Q3 business investment"),
    ("56", "goals in 18 Europa League games"),
]

# Region bar (v4, World Dispatch categories): counts recomputed from the
# actual 40-story set (STORIES-VERIFIED.md). Mapping: 05/34/35/40 -> N.AM;
# 12 -> LAT.AM; 04/07/09/14/18/19/20/21/22/23/25/26/28/31 -> EUROPE;
# 06/11 -> RUSSIA-UKRAINE; 02/32 -> AFRICA; 01/03/24/33/38/39 -> MID.EAST;
# 13/16/29 -> S.ASIA; 10/15/17/27/30 -> E.ASIA; 08/36/37 -> SE ASIA;
# OCEANIA has no story in the 40. The 10 counts sum to 40.
REGION_BAR = [
    ("N. AMERICA", 4, NAVY),
    ("LATIN AMERICA", 1, TERRA),
    ("EUROPE", 14, PURPLE),
    ("RUSSIA-UKRAINE", 2, MAROON),
    ("AFRICA", 2, MUSTARD_DK),
    ("MIDDLE EAST", 6, TEAL),
    ("SOUTH ASIA", 3, NAVY),
    ("EAST ASIA", 5, TEAL_DK),
    ("SE ASIA", 3, MUSTARD_DK),
    ("OCEANIA", 0, SKY_DK),
]

TIMELINE = [
    ("01:00", "BoK hikes to 3.25%"),
    ("02:35", "Yoon acquittal"),
    ("07:00", "GfK −30.2 published"),
    ("10:30", "BoE Stability Report"),
    ("12:08", "Progress 97 docks"),
]

ALSO = [
    ("EUROPE", [
        ("14", "Meloni warns on warship sinking", "BBC"),
        ("18", "NHS flu admissions up 80% in a week", "BBC"),
        ("19", "92 Labour MPs oppose Rosebank field", "BBC"),
        ("20", "UK to pay 4% fee in EU treaties", "BBC"),
        ("21", "Huntingdon attacker guilty, 14 counts", "BBC"),
        ("22", "Depardieu to stand trial for rape", "Reuters"),
        ("23", "Mandelson kept lobby shares as envoy", "BBC"),
        ("25", "German dealer 'armed Channel gangs'", "BBC"),
        ("26", "UK £8bn submarine deal: 3,000 jobs", "MoD"),
        ("28", "Serbia vote set for 27 Dec", "Reuters"),
        ("31", "Besiktas match halted after clashes", "UEFA"),
    ]),
    ("ASIA", [
        ("15", "Taiwan sergeant jailed for spying", "Taipei Times"),
        ("16", "Mumbai marks 18 years since 26/11", "AirNews"),
        ("17", "China–Japan ships clash near Senkaku", "AFP"),
        ("27", "Hong Kong marks Tai Po fire anniversary", "AP"),
        ("29", "India proposes Parliament sitting", "PTI"),
        ("30", "China: India border 'stable'", "Def Min"),
    ]),
    ("MIDDLE EAST", [
        ("24", "Six women on death row in Iran", "BBC"),
    ]),
]

# Borderline: events from earlier days, first reported / developed 26 Nov.
REPORTED = [
    ("32", "DR Congo summons Uganda envoy", "BBC"),
    ("33", "Houthi attacks on Saudi ports", "Reported"),
    ("34", "US tariffs: China +20%, EU 15–20%", "BBC"),
    ("35", "FCC clears SpaceX 1M satellites", "BBC"),
    ("36", "Bogor mine flood: 13 dead, 13 missing", "BBC"),
    ("37", "Philippine Coast Guard gets 3 vessels", "GMA"),
    ("38", "Kushner: drop the war mindset", "Reported"),
    ("39", "Egypt detains Giza tanker driver", "NY Ed"),
    ("40", "GAO: munitions rebuild takes years", "Fortune"),
]

# Flat Also list (v4, World Dispatch): stories 13-40 in numerical order.
# #13 India-UAE moved here from FEATURES; ALSO (18) + REPORTED (9) + #13 = 28.
_also_flat = [("13", "India–UAE fast-track defence kit", "Defence Ministry")]
for _group in ALSO:
    _also_flat.extend(_group[1])
_also_flat.extend(REPORTED)
ALSO_V4 = sorted(_also_flat, key=lambda t: int(t[0]))

# ------------------------------------------------------------------ layout
def _truncate(pg, text, font, max_w):
    if pg.text_w(text, font) <= max_w:
        return text
    while text and pg.text_w(text + " ...", font) > max_w:
        text = text[:-1].rstrip()
    return text + " ..."


def _also_item(pg, x, y, num, head, src, font, num_font, max_w):
    """One 'Also on Thursday' line: number + headline (no source — Grand
    Obelisk has no per-item source in the Also list)."""
    pg.text(x, y, num, num_font, TERRA)
    nx = x + pg.text_w(num + "  ", num_font)
    rest = _truncate(pg, head, font, max_w - (nx - x))
    pg.text(nx, y, rest, font, INK)


def draw_top(pg):
    """Masthead (v8): "THE WORLD IN ONE DAY" top (from v5/v7) over the v6
    Grand Obelisk body. Top bar + huge date + terracotta sub-headline,
    then the 6-STAT ROW (v8 — the numbers at the top, below the
    sub-headline, as in the reference top crop), then the dark teal
    strip with the 3 lead headlines, each preceded by a "•" bullet.

    The v6 "World Dispatch" masthead is REMOVED (the user asked where
    the "THE WORLD IN ONE DAY" top is). There is only ONE masthead.
    The reference top's region bar / Day-in-UTC strip are NOT re-added —
    those sections already exist in the Grand Obelisk body.
    """
    # --- top bar: "THE WORLD IN ONE DAY" + story count, right-aligned
    f_top = F.serif_bold(s(14))
    pg.text(M, s(6), "THE WORLD IN ONE DAY", f_top, INK)
    f_cnt = F.sans_bold(s(10))
    pg.text(W - M, s(8), "40 DATED STORIES · 10 REGIONS · ALL FROM "
            "THURSDAY 26 NOVEMBER 2026", f_cnt, INK, anchor="ra")
    # --- the date itself, HUGE editorial serif, full width
    f_title, _sz = pg.fit("Thursday 26 November 2026", F.serif_bold, s(46),
                          CW, min_size=s(30))
    pg.text(M, s(22), "Thursday 26 November 2026", f_title, INK)
    # --- sub-headline: Georgia Italic, terracotta, centred (v5 verbatim)
    sub = ("60 mph gusts ground Macy's 100th parade · EU leaders clash on "
           "€45bn Kyiv loan · Korea hikes rate to 3.25% as tech rebounds")
    f_sub, _sz2 = pg.fit(sub, F.serif_italic, s(13), CW - s(16),
                         min_size=s(9))
    pg.text(W // 2, s(76), sub, f_sub, TERRA, anchor="ma")
    # --- 6-stat row (v8): large brick-RED numbers, small INK captions
    # below, left-aligned per column, evenly spaced across the width —
    # as in the reference top crop. Verified numbers only (see TOP_STATS).
    st_qw = CW // 6
    f_stc = F.sans_reg(s(9))
    for i, (num, cap) in enumerate(TOP_STATS):
        x = M + i * st_qw
        w = st_qw if i < 5 else CW - 5 * st_qw
        f_n, _szn = pg.fit(num, F.sans_bold, s(24), w - s(8),
                           min_size=s(12))
        pg.text(x, s(92), num, f_n, RED)
        cap_t = _truncate(pg, cap, f_stc, w - s(8))
        pg.text(x, s(118), cap_t, f_stc, INK)
    # --- dark teal strip: the 3 lead headlines, each preceded by a bullet
    strip_y = s(132)
    strip_h = s(26)
    pg.rect(M, strip_y, CW, strip_h, DARK_TEAL)
    strip = ("• Two Italians killed in Kuwait drone strike • DR Congo "
             "Ebola passes 12,000 • Israel kills Hamas official in Gaza")
    f_st, sz_st = pg.fit(strip, F.sans_bold, s(16), CW - s(16),
                         min_size=s(10))
    pg.text(W // 2, strip_y + (strip_h - sz_st) // 2, strip, f_st, WHITE,
            anchor="ma")


def draw_cards(pg):
    """12 illustrated cards (v6, Grand Obelisk): 3 LARGE lead cards on the
    top row (illustration on top, large headline), then 3 rows x 3 SMALLER
    feature cards (illustration on the LEFT, text on the right).

    Each card: number badge (white square, top-left of the illustration),
    location in RED capitals + status tag (filled, top-right), Georgia Bold
    headline, Arial summary. NO source line per card (Grand Obelisk has none).
    """
    gap_x = s(6)
    gap_y = s(4)
    cw = (CW - 2 * gap_x) // 3
    # --- top row: 3 large lead cards
    y0 = s(162)
    large_h = s(182)
    ill_h = s(96)
    for idx in range(3):
        card = CARDS[idx]
        x = M + idx * (cw + gap_x)
        y = y0
        pg.rrect(x, y, cw, large_h, s(5), CARD, outline=RULE_LT, width=s(1))
        _clip_draw(pg, card["draw"], x + s(1), y + s(1), cw - s(2), ill_h)
        chip(pg, x + s(4), y + s(4), card["num"], WHITE, INK, size=14)
        ly = y + ill_h + s(6)
        f_loc = F.sans_bold(s(11))
        pg.text(x + s(8), ly, card["loc"], f_loc, RED)
        st = card["status"]
        f_st = F.sans_bold(s(10))
        tag_w = pg.text_w(st, f_st) + 2 * s(6)
        tag_sm(pg, x + cw - s(8) - tag_w, ly, st, STATUS_BG[st], size=10)
        hy = ly + s(20)
        f_h = F.serif_bold(s(16))
        end = pg.para(x + s(8), hy, card["head"], f_h, INK, cw - s(16), 2,
                      s(16))
        f_s = F.sans_reg(s(10))
        pg.para(x + s(8), end + s(2), card["summ"], f_s, GREY, cw - s(16),
                2, s(11))
    # --- below: 3 rows x 3 smaller cards, illustration on the left
    small_h = s(82)
    sy0 = y0 + large_h + gap_y
    ill_sq = s(76)
    for idx in range(3, 12):
        r, c = divmod(idx - 3, 3)
        card = CARDS[idx]
        x = M + c * (cw + gap_x)
        y = sy0 + r * (small_h + gap_y)
        pg.rrect(x, y, cw, small_h, s(5), CARD, outline=RULE_LT, width=s(1))
        _clip_draw(pg, card["draw"], x + s(4), y + s(4), ill_sq, ill_sq)
        chip(pg, x + s(7), y + s(7), card["num"], WHITE, INK, size=12)
        tx = x + ill_sq + s(12)
        tw = cw - ill_sq - s(20)
        ly = y + s(6)
        f_loc = F.sans_bold(s(10))
        pg.text(tx, ly, card["loc"], f_loc, RED)
        st = card["status"]
        f_st = F.sans_bold(s(10))
        tag_w = pg.text_w(st, f_st) + 2 * s(6)
        tag_sm(pg, x + cw - s(8) - tag_w, ly, st, STATUS_BG[st], size=10)
        hy = ly + s(20)
        f_h = F.serif_bold(s(14))
        end = pg.para(tx, hy, card["head"], f_h, INK, tw, 2, s(15))
        f_s = F.sans_reg(s(10))
        pg.para(tx, end + s(1), card["summ"], f_s, GREY, tw, 2, s(11))


def draw_stats_band(pg):
    """Dark teal stats band (v6, Grand Obelisk): 4 verified stats.

    Large gold (MUSTARD) numbers + white captions, one per quarter.
    Sits in the middle of the page, after the 12 cards, before Also.
    """
    y0 = s(608)
    h = s(36)
    pg.rect(M, y0, CW, h, DARK_TEAL)
    qw = CW // 4
    f_l = F.sans_reg(s(9))
    for i, (num, label, col) in enumerate(STATS):
        x = M + i * qw
        w = qw if i < 3 else CW - 3 * qw
        f_n, _sz = pg.fit(num, F.sans_bold, s(26), w - s(16),
                          min_size=s(12))
        pg.text(x + s(8), y0 + s(2), num, f_n, col)
        cap = _truncate(pg, label, f_l, w - s(16))
        pg.text(x + s(8), y0 + s(25), cap, f_l, WHITE)


def draw_also(pg):
    """Also on Thursday (v6, Grand Obelisk): header, 10-region bar,
    then a flat 3-column list of stories 13-40 (28 items), no per-item
    source."""
    y0 = s(652)
    f_h = F.serif_bold(s(14))
    pg.text(M, y0, "ALSO ON THURSDAY", f_h, INK)
    f_n = F.sans_bold(s(11))
    pg.text(W - M, y0 + s(2), "28 MORE DISPATCHES / 10 REGIONS IN THIS "
            "EDITION", f_n, TERRA, anchor="ra")
    pg.rect(M, y0 + s(18), CW, s(1), INK)
    # --- region bar (10 equal segments; counts sum to 40)
    ry = s(674)
    seg = CW // 10
    f_reg = F.sans_bold(s(8))
    for i, (name, cnt, col) in enumerate(REGION_BAR):
        x = M + i * seg
        w = seg if i < 9 else CW - 9 * seg
        pg.rect(x, ry, w, s(18), col)
        lab = "%s %d" % (name, cnt)
        tw = pg.text_w(lab, f_reg)
        pg.text(x + (w - tw) // 2, ry + s(5), lab, f_reg, WHITE)
    # --- flat 3-column list, stories 13-40 in numerical order (10/9/9)
    col_w = (CW - 2 * s(10)) // 3
    f_item = F.sans_reg(s(10))
    f_num = F.sans_bold(s(10))
    lh = s(10)
    cols = [ALSO_V4[0:10], ALSO_V4[10:19], ALSO_V4[19:28]]
    for ci, items in enumerate(cols):
        x = M + ci * (col_w + s(10))
        iy = s(698)
        for num, head, src in items:
            _also_item(pg, x, iy, num, head, src, f_item, f_num, col_w)
            iy += lh


def draw_bottom(pg):
    """Bottom row (v6, Grand Obelisk): large dark map | Day in UTC |
    Date Check (earlier events). Taller than v4 — the map is large.
    v9: UTC + Date Check enlarged (bigger fonts, wider line spacing)
    so they span the full map height — v8 left a large blank cream
    area below them."""
    y0 = s(802)
    h = s(182)
    # --- story locator map (left, large, dark teal)
    mw = s(360)
    f_h = F.sans_bold(s(12))
    pg.text(M, y0, "STORY LOCATOR", f_h, NAVY)
    f_ill = F.sans_bold(s(10))
    pg.text(M + mw, y0, "ILLUSTRATED REPORTS 01–12", f_ill, RED,
            anchor="ra")
    draw_map_dark(pg, M, y0 + s(22), mw, h - s(22))
    # --- the day in UTC (middle, 5 verified nodes, one per line;
    # times in RED, as in Grand Obelisk). v9: enlarged so the 5 nodes
    # fill the row height down to the footer.
    ux = M + mw + s(16)
    uw = s(260)
    pg.text(ux, y0, "THE DAY IN UTC", f_h, NAVY)
    f_t = F.sans_bold(s(14))
    f_l = F.sans_reg(s(14))
    iy = y0 + s(22)
    for tm, label in TIMELINE:
        pg.text(ux, iy, tm, f_t, RED)
        pg.text(ux + pg.text_w(tm + "  ", f_t), iy, label, f_l, GREY)
        iy += s(31)
    # --- date check (right, earlier-events framing; all dates RED).
    # v9: enlarged to match the UTC column.
    dx = ux + uw + s(16)
    dw = W - M - dx
    pg.text(dx, y0, "DATE CHECK", f_h, RED)
    f_e = F.sans_bold(s(10))
    pg.text(dx + dw, y0, "EARLIER EVENTS", f_e, MUTED, anchor="ra")
    f_d = F.sans_reg(s(14))
    iy = y0 + s(22)
    for date, event, dcol in (("25 NOV", "Giza tanker blast.", RED),
                              ("25 NOV", "EU energy-ban deal.", RED),
                              ("25 NOV", "Shenzhou-24 launch.", RED),
                              ("25 NOV", "US GDP & PCE.", RED),
                              ("26 NOV", "All 40 reports.", RED)):
        pg.text(dx, iy, date, f_t, dcol)
        pg.text(dx + pg.text_w(date + "  ", f_t), iy, event, f_d, INK)
        iy += s(31)


def draw_sources(pg):
    """Footer (v4, World Dispatch): dark band with the sources line (left)
    and the status-tag legend (right). The sources are truncated (with
    ellipsis) only if they would reach the legend, so the two never overlap.
    """
    y0 = s(990)
    h = s(20)
    pg.rect(M, y0, CW, h, DARK_TEAL)
    f_s = F.sans_reg(s(7))
    legend = ("OFFICIAL authority / CLAIM attributed / CLOSE final prices / "
              "REPORT press")
    lw = pg.text_w(legend, f_s)
    srcs = ("Sources: Reuters • BBC • AP • AFP • Xinhua • Interfax • ONS • "
            "UKHSA • MoD • UEFA • NASA • GfK • ABS • Field Level Media • "
            "Bank of England • European Council • Taipei Times • PTI • "
            "Fortune")
    srcs = _truncate(pg, srcs, f_s, CW - s(16) - lw - s(16))
    pg.text(M + s(8), y0 + s(6), srcs, f_s, WHITE)
    pg.text(W - M - s(8), y0 + s(6), legend, f_s, WHITE, anchor="ra")


def build():
    pg = Page()
    draw_top(pg)
    draw_cards(pg)
    draw_stats_band(pg)
    draw_also(pg)
    draw_bottom(pg)
    draw_sources(pg)
    return pg.img


def main():
    import hashlib
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", ".")
    os.makedirs(out_dir, exist_ok=True)
    img = build()
    small = img.resize((1024, 1024), Image.LANCZOS)
    path = os.path.join(out_dir, "entry.png")
    small.save(path, format="PNG", optimize=True)
    data = open(path, "rb").read()
    print("wrote", path)
    print("sha256", hashlib.sha256(data).hexdigest())
    print("bytes", len(data))
    print("size", small.size)


if __name__ == "__main__":
    main()
