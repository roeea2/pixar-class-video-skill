# Hebrew / RTL Title & Caption Cards

On-screen text is drawn with Pillow and overlaid by ffmpeg. Hebrew (and any RTL
text) needs care.

## Fonts (macOS examples)

- `SFHebrewRounded.ttf` (rounded, friendly) — `/System/Library/Fonts/`
- Fallback for Latin: `Arial Rounded Bold.ttf` —
  `/System/Library/Fonts/Supplemental/`

Switch font per run depending on whether the run is Hebrew or Latin/digits.

## RTL handling

Pillow does not reorder RTL text. Reverse runs manually, keeping Latin/number
runs in their own order:

```python
import re
def rtl(s):
    return ''.join(reversed(re.findall(r'[0-9A-Za-z]+|.', s)))
```

So `שנת 2026` renders correctly and the digits `2026` stay in order (not mirrored).

## The `?` / tofu gotcha

`SFHebrewRounded` lacks a `?` glyph — it renders as a tofu box. **Use `!`
instead.** Test any punctuation before shipping a card.

## Card style that works

- 1920×1080, dark navy vertical-gradient background.
- Title in warm **gold**, subtitle in **white**, both with a soft drop shadow.
- Caption cards: small white kicker line + large gold line.
- Center text; keep generous margins.

## Transparent overlay

For segments that need **no** caption, use a fully transparent `blank.png`
(1920×1080 RGBA, all alpha 0) as the overlay so the pipeline stays uniform.

## Generator

`scripts/make_title_card.py` builds title and caption PNGs. Example:

```
python3 scripts/make_title_card.py title "כיתה ו׳" "סרט סוף השנה" titles/t_intro.png
python3 scripts/make_title_card.py caption "" "<שם> מנגן בגיטרה" titles/c_guitar.png
python3 scripts/make_title_card.py blank titles/blank.png
```

The overlay is faded in/out by the assembler (see assembly-and-music.md).
