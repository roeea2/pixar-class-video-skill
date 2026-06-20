#!/usr/bin/env python3
"""
make_caption.py — render a per-scene SUBTITLE / text-over as a transparent PNG to
composite over a clip (lower third, translucent panel, RTL-aware).

Usage:
  make_caption.py --size 1080x1920 "<main line>" out.png
  make_caption.py --size 1920x1080 --kicker "<small white line>" --line2 "<2nd gold line>" "<main>" out.png

Options:
  --size WxH     canvas (match the video). default 1080x1920 (vertical reel)
  --gold #RRGGBB accent colour (default #F4C44E)
  --font <path>  override the Hebrew display font

RTL is handled per-character (Hebrew font for Hebrew, Latin font for digits/Latin)
so "PM", "24/7", years, etc. render correctly. SF Hebrew Rounded lacks "?" — use "!".
"""
import sys, os, re
from PIL import Image, ImageDraw, ImageFont

def arg(flag, default=None):
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else default

SIZE = arg("--size", "1080x1920"); W, H = (int(x) for x in SIZE.lower().split("x"))
GOLD = arg("--gold", "#F4C44E"); WHITE = "#FFFFFF"
KICKER = arg("--kicker"); LINE2 = arg("--line2")
HEB_OVERRIDE = arg("--font")
# positional args (text + out) after flags are stripped
pos = [a for k, a in enumerate(sys.argv[1:])
       if not a.startswith("--") and sys.argv[k] not in
       ("--size", "--gold", "--kicker", "--line2", "--font")]
if len(pos) < 2:
    raise SystemExit(__doc__)
MAIN, OUT = pos[0], pos[1]

HEB = [HEB_OVERRIDE, "/System/Library/Fonts/SFHebrewRounded.ttf",
       "/System/Library/Fonts/SFHebrew.ttf",
       "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
LAT = ["/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf",
       "/Library/Fonts/Arial.ttf",
       "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
def pick(c):
    for p in c:
        if p and os.path.exists(p): return p
    raise SystemExit("no font found; pass --font")
HEBF, LATF = pick(HEB), pick(LAT)

def hexc(s): return tuple(int(s.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + (255,)
def is_heb(c): return "֐" <= c <= "׿" or "יִ" <= c <= "ﭏ"
def rtl(s):
    if not any(is_heb(c) for c in s): return s
    return "".join(reversed(re.findall(r"[0-9A-Za-z/.:]+|.", s)))

def draw_line(d, text, y, size, fill):
    hf = ImageFont.truetype(HEBF, size); lf = ImageFont.truetype(LATF, size)
    t = rtl(text); f = lambda c: hf if is_heb(c) else lf
    x = (W - sum(d.textlength(c, font=f(c)) for c in t)) / 2
    for c in t:
        ff = f(c)
        d.text((x + 3, y + 4), c, font=ff, fill=(0, 0, 0, 170))
        d.text((x, y), c, font=ff, fill=fill)
        x += d.textlength(c, font=ff)

def measure(d, text, size):
    hf = ImageFont.truetype(HEBF, size); lf = ImageFont.truetype(LATF, size)
    return sum(d.textlength(c, font=hf if is_heb(c) else lf) for c in rtl(text))

img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)

base = max(40, int(W * 0.075))            # main font size scales with width
def build(b):
    ls = []
    if KICKER: ls.append((KICKER, int(b * 0.55), hexc(WHITE)))
    ls.append((MAIN, b, hexc(GOLD)))
    if LINE2: ls.append((LINE2, b, hexc(GOLD)))
    return ls
lines = build(base)
# auto-shrink so the widest line fits within 88% of the width
widest = max(measure(d, t, s) for t, s, _ in lines)
if widest > 0.88 * W:
    base = max(28, int(base * 0.88 * W / widest))
    lines = build(base)
line_h = [int(s * 1.25) for _, s, _ in lines]
block = sum(line_h) + int(base * 0.33) * (len(lines) - 1)
maxw = max(measure(d, t, s) for t, s, _ in lines)
y0 = int(H * 0.64) - block // 2           # lower third
padx, pady = int(base * 0.6), int(base * 0.5)
d.rounded_rectangle([(W - maxw) / 2 - padx, y0 - pady,
                     (W + maxw) / 2 + padx, y0 + block + pady],
                    radius=int(base * 0.45), fill=(12, 16, 28, 165))
y = y0
for (t, s, col), lh in zip(lines, line_h):
    draw_line(d, t, y, s, col); y += lh + int(base * 0.33)
img.save(OUT)
print("wrote", OUT, f"({W}x{H})")
