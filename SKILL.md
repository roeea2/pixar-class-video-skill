---
name: pixar-class-video
description: "Interactive director for building a beautiful Pixar-style end-of-year class video (Hebrew or any language). Use this skill when the user wants to create a class movie, end-of-year video, 'סרט סוף שנה', turn kids' photos into Pixar characters, animate hobby scenes, add RTL/Hebrew title cards, assemble clips with music, or build a teaser/promo. Walks the user STEP BY STEP, asking what to do at each phase, and uses the Higgsfield MCP for images/video + ffmpeg for assembly."
argument-hint: "[start|kid|cards|assemble|teaser] <optional note>"
metadata:
  version: "1.0.0"
  author: RoeeAI
  requires: "Higgsfield MCP, ffmpeg, ffprobe, python3 (PIL)"
---

# Pixar Class Video — Step-by-Step Director

Turn a class roster of photos + hobbies into a polished ~7–10 minute Pixar-style
movie: every child as a faithful 3D character, animated hobby scenes, RTL Hebrew
title/caption cards, real-photo interludes, a rotating soundtrack, a whole-class
finale, and a teaser for parents.

This skill is a **guided wizard**. You (Claude) act as the director and **ask the
user before each phase** — never batch the whole movie silently. Confirm scope,
show results, get a thumbs-up, then continue.

## MANDATORY — read before generating anything

Before constructing any image/video prompt, read:
1. `references/likeness-recipe.md` — how to make characters actually resemble the kids
2. `references/prompt-gotchas.md` — the failure modes (NSFW false-flags, dark-skin fillers, duplicated people, fat/braces artifacts, eye color, lighting) and their fixes
3. `references/higgsfield-pipeline.md` — exact MCP tools, models, params, polling
4. `references/hebrew-titles.md` — RTL title cards with PIL (the `?`/tofu gotcha)
5. `references/assembly-and-music.md` — the 2-chunk ffmpeg assembler + music rotation + the silent-truncation bug

Do not skip these even for a "quick" request. They encode hard-won fixes.

## The golden rules (do not violate)

- **Likeness first.** The user cares most that each character looks like the real
  child. After every character sheet, show it and ask "close enough?" before
  building that kid's scenes. Re-roll on request.
- **One child per solo scene.** Always add "Exactly ONE child alone, no other
  people" or the model duplicates them.
- **Always verify the render.** After every assembly, compare the VIDEO stream
  duration to the AUDIO stream duration (`ffprobe -select_streams v:0`). A long
  xfade chain can silently truncate the tail with rc=0. See assembly doc.
- **Ask, show, confirm.** Each phase ends with a preview and a question.
- **Privacy.** These are real minors. Never upload the kids' photos anywhere
  except the generation API the user already chose. If publishing/teaser-sharing,
  warn before putting real faces on any public surface.

## Quick command map

| Invocation | What you do |
|---|---|
| `/pixar-class-video` or `start` | Run the full wizard from Phase 0 |
| `kid <name>` | Add/redo a single child (sheet → verify → scenes → animate) |
| `cards` | (Re)generate Hebrew/RTL title + caption cards |
| `assemble` | Rebuild the movie and verify video==audio |
| `teaser` | Build/refresh the parents' teaser |

---

## Phase 0 — Setup & scope (ASK FIRST)

1. Confirm prerequisites: Higgsfield MCP available (`balance` works), `ffmpeg`,
   `ffprobe`, `python3` with Pillow. If missing, tell the user what to install.
2. Create a workspace: `video_assets/{clips,titles,characters,images,music}` and a
   scratch dir like `/tmp/<project>`.
3. **Ask the user these scoping questions** (use the AskUserQuestion tool):
   - Language of the on-screen text (Hebrew RTL? other?).
   - Target length / how many kids.
   - Music vibe (and confirm any "must-open-with" track).
   - How many hobby scenes per child (1–3).
   - Output filename.
4. Restate the plan in one paragraph and get a go-ahead.

## Phase 1 — Collect the roster (ASK)

Ask the user to provide, per child: **name** (in the target language), a clear
**face photo** (`self.*`), and **1–3 hobbies**. A folder-per-child layout works
well. Confirm the order kids will appear. Do NOT invent hobbies — ask.

## Phase 2 — Per-child pipeline (LOOP, confirm each)

For each child, in order, do this and **stop to show the character sheet**:

1. Crop the face from `self.*` (square, centered). Upload via the pipeline in
   `references/higgsfield-pipeline.md` (`media_upload` → PUT → `media_confirm`).
2. Generate a **character sheet** using `references/likeness-recipe.md` (state the
   real age, face shape, exact hair/eye color, distinguishing marks; demand "only
   mild stylization, not a generic cartoon child").
3. **Show it to the user. Ask: does this look like <name>?** Re-roll until yes.
   Save the approved sheet to `video_assets/characters/char_<name>.png`.
4. Generate a **hero/title shot** + the **hobby scene(s)** seeded by the approved
   sheet. One child alone. Apply `references/prompt-gotchas.md`.
5. **Animate** each still (kling, 5s) — see pipeline doc. Download to
   `video_assets/clips/<name>_<scene>.mp4`.
6. Briefly confirm the clips, then move to the next child.

> Re-doing one kid later? Use `kid <name>` — only that child's sheet+scenes are
> regenerated and swapped into the assembly list; nothing else changes.

## Phase 3 — Title & caption cards (Hebrew/RTL)

Use `scripts/make_title_card.py` (see `references/hebrew-titles.md`). Generate a
name title card per child and a caption card per scene. Mind the RTL reversal and
the missing-`?` glyph (use `!`). Use a fully transparent `blank.png` for segments
that need no caption.

## Phase 4 — Group scenes, events & real-photo interludes (ASK)

- Whole-class **finale** ("see you next year…"), plus any **event** recreations
  (trips, parties) and **group** scenes. Seed 4–6 distinctive character refs;
  follow the crowd/skin-tone guidance in `references/prompt-gotchas.md`.
- For authenticity, play the **real photo** right before each recreated scene
  (`scripts/make_real_clip.py` → blurred-fill + zoompan). **Ask** the user which
  real photos to use; warn that real faces will appear.
- Decide the ending: many users end on real class photos, then a closing card.

## Phase 5 — Music (ASK)

Confirm tracks (royalty-free, e.g. Kevin MacLeod CC-BY — credit on the end card).
The assembler rotates tracks every ~55s so it never drags; it can open with a
required favorite. See `references/assembly-and-music.md`.

## Phase 6 — Assemble & VERIFY

Run `scripts/assemble.py` (2-chunk method). Then **always**:

```
ffprobe -v error -select_streams v:0 -show_entries stream=duration,nb_frames -of default=nk=1:nw=1 OUT.mp4
ffprobe -v error -select_streams a:0 -show_entries stream=duration            -of default=nk=1:nw=1 OUT.mp4
```

Video and audio durations must match (within ~1 frame). If video is short, the
xfade chain truncated — split into more chunks (see doc). Show the user the final
length + a couple of spot-checked frames.

## Phase 7 — Teaser (ASK)

Offer a short promo with `scripts/make_teaser.py`: title card → fast montage of
the best moments → finale → end card, over the opening track, hard cuts to hit an
exact duration. Costs 0 generation credits (pure ffmpeg). Confirm length (15–20s)
and whether to include real photos.

---

## Failure-mode cheat sheet (full details in references/)

- **"NSFW" on a child image** → rephrase to "wholesome Pixar-style 3D animated
  movie character of a cheerful schoolchild." Retry.
- **Random dark-skinned filler kids in crowds** → remove the word "diverse";
  state the actual class skin tones explicitly; re-pass if needed.
- **Person duplicated** → "Exactly ONE child alone, no other people."
- **Character rendered fat / with braces / wrong eye color** → drop the
  over-strong ref, add the corrective adjective ("slim", "no braces", "blue eyes").
- **Too dark from golden-hour light** → "bright even midday daylight."
- **Tail of the movie missing though rc=0** → xfade chain truncation; use more
  chunks and re-verify video==audio.

Keep the user in the loop, keep characters faithful, and verify every render.
