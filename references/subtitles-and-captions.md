# Subtitles & Text-Over (per-scene captions)

Two kinds of on-screen text in this pipeline:

1. **Title / name cards** — full-frame cards between segments (see
   `hebrew-titles.md` + `make_title_card.py`).
2. **Subtitles / text-over** — a caption laid **over** a scene while it plays
   (lower third), e.g. the spoken line or a key phrase. That's this doc +
   `make_caption.py`.

## Caption overlay style that works

- Transparent PNG the size of the video (e.g. `1080x1920` vertical, `1920x1080`
  landscape), composited over the clip.
- A **translucent rounded panel** (dark, alpha ≈ 150–170) behind the text so it
  stays readable over busy footage.
- Text in warm **gold** (and an optional white kicker/second line), centered,
  with a soft drop shadow. 1–2 lines; keep it short.
- Place it in the **lower third**, but above the platform safe area: for 9:16
  reels keep the panel centred around y ≈ 1150–1450 (clear of the bottom UI).

## RTL + mixed digits/Latin

Reuse the rules from `hebrew-titles.md`: reverse RTL runs while keeping
Latin/number runs in order, and choose the font **per character** (Hebrew font for
Hebrew, a Latin font for digits/Latin) — the rounded Hebrew font has no Latin
digits and renders them as tofu otherwise. `make_caption.py` does this. Test
punctuation (`?` is missing in SF Hebrew Rounded → use `!`).

## Generating overlays

```
# one caption (lower-third), vertical:
python3 scripts/make_caption.py --size 1080x1920 "אין עובדים — רק סוכנים" caps/cap2.png
# two lines + small white kicker:
python3 scripts/make_caption.py --size 1080x1920 --kicker "" --line2 "רק סוכנים" "אין עובדים —" caps/cap2.png
```

## Timing & burn-in

- Per-scene captions are overlaid for that scene's duration with a quick alpha
  fade-in (≈0.3s). `assemble_narrated.py` does this automatically from a
  `narration.txt` (one `clip | caption | vo` line per scene).
- If you want true time-coded subtitles instead (e.g. a long talking clip),
  generate an `.srt` and burn with ffmpeg `subtitles=subs.srt` — but for short,
  one-line-per-scene reels the overlay-PNG approach looks cleaner and handles RTL
  reliably (ffmpeg's libass RTL shaping can be inconsistent).
- Always keep captions in sync with the voiceover: if a scene has VO, its caption
  should be that line (or its gist).
