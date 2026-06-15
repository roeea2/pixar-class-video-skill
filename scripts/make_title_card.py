#!/usr/bin/env python3
"""
make_title_card.py — render Hebrew/RTL (or LTR) title & caption cards as 1920x1080
PNGs for the class-video pipeline. Also makes a fully transparent blank overlay.

Usage:
  make_title_card.py title   "<main>" "<subtitle>" <out.png>
  make_title_card.py caption "<kicker>" "<main>"   <out.png>
  make_title_card.py blank   <out.png>

Options (env or flags):
  --font  <path>   main font (default: auto-detect a Hebrew-capable rounded font)
  --gold  #RRGGBB  accent color (default #F2C14E)
  --bg    #RRGGBB  background base (default #15233F)

RTL is handled by reversing character runs while keeping Latin/number runs intact,
so "שנת 2026" renders correctly. Note: SF Hebrew Rounded lacks "?" — use "!".
"""
import sys, os, re
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
GOLD = "#F2C14E"
WHITE = "#F4F6FB"
BG_TOP = "#15233F"
BG_BOT = "#0C1526"

# Hebrew-capable display fonts (nice rounded look) and Latin/digit fonts.
# SF Hebrew Rounded has NO Latin digits, so digits/Latin are drawn with a Latin
# font per-character — otherwise "3" renders as a tofu box.
HEB_CANDIDATES = [
    "/System/Library/Fonts/SFHebrewRounded.ttf",
    "/System/Library/Fonts/SFHebrew.ttf",
    "/Library/Fonts/Arial Hebrew.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
LAT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf",
    "/Library/Fonts/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
]


def find_one(cands):
    for p in cands:
        if os.path.exists(p):
            return p
    return None


def fonts(size, heb_override=None):
    hp = heb_override or find_one(HEB_CANDIDATES) or find_one(LAT_CANDIDATES)
    lp = find_one(LAT_CANDIDATES) or hp
    if not hp:
        raise SystemExit("No usable font found; pass --font <path>.")
    return ImageFont.truetype(hp, size), ImageFont.truetype(lp, size)


def is_heb_char(c):
    return '֐' <= c <= '׿' or 'יִ' <= c <= 'ﭏ'


def is_heb(s):
    return any(is_heb_char(c) for c in s)


def rtl(s):
    """Reverse RTL string but keep Latin/number runs in natural order."""
    if not is_heb(s):
        return s
    return ''.join(reversed(re.findall(r'[0-9A-Za-z]+|.', s)))


def gradient_bg():
    top = tuple(int(BG_TOP[i:i+2], 16) for i in (1, 3, 5))
    bot = tuple(int(BG_BOT[i:i+2], 16) for i in (1, 3, 5))
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        t = y / (H - 1)
        c = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3))
        for x in range(W):
            px[x, y] = c
    return img.convert("RGBA")


def draw_centered(draw, text, hf, lf, y, fill):
    """Draw RTL-ordered text centered, choosing the Hebrew or Latin font per
    character so digits/Latin (absent from the Hebrew font) render correctly."""
    t = rtl(text)

    def fnt(c):
        return hf if is_heb_char(c) else lf

    total = sum(draw.textlength(c, font=fnt(c)) for c in t)
    x = (W - total) / 2.0
    for c in t:
        f = fnt(c)
        draw.text((x + 3, y + 4), c, font=f, fill=(0, 0, 0, 150))
        draw.text((x, y), c, font=f, fill=fill)
        x += draw.textlength(c, font=f)


def main():
    args = sys.argv[1:]
    heb_override = None
    if "--font" in args:
        i = args.index("--font"); heb_override = args[i+1]; del args[i:i+2]
    if not args:
        raise SystemExit(__doc__)
    mode = args[0]

    if mode == "blank":
        out = args[1]
        Image.new("RGBA", (W, H), (0, 0, 0, 0)).save(out)
        print("wrote", out); return

    img = gradient_bg()
    d = ImageDraw.Draw(img)

    if mode == "title":
        main_t, sub_t, out = args[1], args[2], args[3]
        hf_main, lf_main = fonts(170, heb_override)
        hf_sub, lf_sub = fonts(70, heb_override)
        draw_centered(d, main_t, hf_main, lf_main, H // 2 - 150, GOLD)
        if sub_t:
            draw_centered(d, sub_t, hf_sub, lf_sub, H // 2 + 70, WHITE)
    elif mode == "caption":
        kicker, main_t, out = args[1], args[2], args[3]
        hf_kick, lf_kick = fonts(60, heb_override)
        hf_main, lf_main = fonts(110, heb_override)
        y = H - 360
        if kicker:
            draw_centered(d, kicker, hf_kick, lf_kick, y, WHITE); y += 110
        draw_centered(d, main_t, hf_main, lf_main, y, GOLD)
    else:
        raise SystemExit(__doc__)

    img.save(out)
    print("wrote", out)


if __name__ == "__main__":
    main()
