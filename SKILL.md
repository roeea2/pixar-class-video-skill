---
name: pixar-class-video
description: "Interactive director for building a beautiful Pixar-style end-of-year class video (Hebrew or any language). Use this skill when the user wants to create a class movie, end-of-year video, 'סרט סוף שנה', turn kids' photos into Pixar characters, animate hobby scenes, add RTL/Hebrew title cards, assemble clips with music, or build a teaser/promo. Walks the user STEP BY STEP, asking what to do at each phase, and uses the Higgsfield MCP for images/video + ffmpeg for assembly."
argument-hint: "[start|kid|cards|assemble|teaser] <optional note>"
metadata:
  version: "1.1.0"
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
6. `references/subtitles-and-captions.md` — per-scene subtitles / text-over (when laying captions over scenes)
7. `references/voiceover-and-lipsync.md` — optional spoken narration, voice cloning, and lip-sync (when adding audio/voiceover)

Do not skip these even for a "quick" request. They encode hard-won fixes.

## The golden rules (do not violate)

- **Likeness first.** The user cares most that each character looks like the real
  child (or, for a personal reel, themselves). After every character sheet, show it
  and ask "close enough?" before building that person's scenes. Re-roll on request.
- **Let the reference define appearance — never override it in the prompt.** Once a
  canonical character sheet/reference exists, pass it to every downstream scene and
  describe only the *action and setting*. Do NOT restate hair, clothes, glasses, age,
  or face in words that differ from the reference (e.g. don't write "navy blazer,
  short dark hair" when the reference is an orange polo and a buzz-cut) — the model
  obeys the words and silently produces a different-looking person. If the user wants
  to *change* the look, change the reference first, lock it, then generate scenes.
- **One child per solo scene.** Always add "Exactly ONE child alone, no other
  people" or the model duplicates them.
- **Always verify the render.** After every assembly, compare the VIDEO stream
  duration to the AUDIO stream duration (`ffprobe -select_streams v:0`). A long
  xfade chain can silently truncate the tail with rc=0. See assembly doc.
- **Ask, show, confirm — one approval gate per artifact.** Never batch a whole reel.
  Render → show the user the actual result → wait for an explicit OK → only then spend
  on the next step. The gate order for a character reel is: (1) **character look**
  (lock the likeness), (2) **each scene still**, (3) **animation**, (4) **voice sample**,
  (5) **lip-sync**, (6) **final assembly**. Getting an OK on a cheap still saves
  re-rolling every expensive clip after it.
- **Ask for credentials up front.** If a step needs a key (ElevenLabs, etc.), say so
  and request it before starting — don't silently fall back to a lesser path or stall.
  A pasted key is exposed: store it only in an env var / a `/tmp` file (chmod 600),
  never in the repo, and tell the user to rotate it afterward.
- **Verify TTS language.** If you add voiceover, never trust that the model spoke
  the right language — transcribe a sample with `openai-whisper` and check the
  detected language (e.g. ElevenLabs `multilingual_v2` silently speaks Persian for
  Hebrew text; only `eleven_v3` does Hebrew). See voiceover-and-lipsync.md.
- **Privacy.** These are real minors (and any cloned voice is real PII). Never
  upload photos/voice anywhere except the generation/TTS service the user chose.
  Keep API keys in env vars only — never write them to a file or commit them. If
  publishing/teaser-sharing, warn before putting real faces/voices on any public
  surface.

## Quick command map

| Invocation | What you do |
|---|---|
| `/pixar-class-video` or `start` | Run the full wizard from Phase 0 |
| `kid <name>` | Add/redo a single child (sheet → verify → scenes → animate) |
| `cards` | (Re)generate Hebrew/RTL title + caption cards |
| `subtitles` | Add per-scene subtitles / text-over a scene (`make_caption.py`) |
| `voiceover` | Add optional narration — TTS, the user's cloned voice, and/or lip-sync |
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
   - **Voiceover?** none (music + cards only) / TTS narration / the user's own
     **cloned** voice — and whether on-camera characters should be **lip-synced**.
   - **Subtitles / text-over** the scenes, or title cards only?
   - Aspect ratio (16:9 / 9:16 / 1:1) and output filename.
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

## Phase 3 — Title cards & subtitles (Hebrew/RTL)

- **Full-frame cards:** `scripts/make_title_card.py` (see `references/hebrew-titles.md`)
  for the name/title cards and any caption cards. Mind the RTL reversal and the
  missing-`?` glyph (use `!`). Use a transparent `blank.png` for segments needing
  no caption.
- **Per-scene subtitles / text-over** (a caption laid over a scene while it plays):
  `scripts/make_caption.py` (see `references/subtitles-and-captions.md`) — a
  lower-third translucent panel, RTL-aware, auto-fits the width, vertical or
  landscape. If a scene has voiceover, its subtitle should be that spoken line.

## Phase 4 — Group scenes, events & real-photo interludes (ASK)

- Whole-class **finale** ("see you next year…"), plus any **event** recreations
  (trips, parties) and **group** scenes. Seed 4–6 distinctive character refs;
  follow the crowd/skin-tone guidance in `references/prompt-gotchas.md`.
- For authenticity, play the **real photo** right before each recreated scene
  (`scripts/make_real_clip.py` → blurred-fill + zoompan). **Ask** the user which
  real photos to use; warn that real faces will appear.
- Decide the ending: many users end on real class photos, then a closing card.

## Phase 5 — Audio: music, voiceover & lip-sync (ASK)

- **Music** (always): confirm royalty-free tracks (e.g. Kevin MacLeod CC-BY —
  credit on the end card). The music-only `assemble.py` rotates tracks every ~55s
  so it never drags; it can open with a required favorite. See
  `references/assembly-and-music.md`.
- **Voiceover** (optional — only if the user wants it): generate one line per scene
  with `scripts/make_voiceover.py`. Backends: macOS `say` (free), ElevenLabs
  (`eleven_v3` is the ONLY model that speaks Hebrew — clone the user's voice with
  `--clone sample.mp3`, paid plan), or Higgsfield Inworld (`Oren`/`Yael` Hebrew
  voices, no key, via the generate_audio tool). **Verify the language with
  `--verify` (whisper).** See `references/voiceover-and-lipsync.md`.
- **Lip-sync** (optional): only `wan2_7` accepts an audio input — feed it the
  scene image + the VO line so the character mouths the words. Kling cannot do
  this. Extract the synced audio back out and use it as that scene's VO so the mix
  lines up with the lips.
- **Mixing:** when there's voiceover/subtitles, assemble with
  `scripts/assemble_narrated.py` (per-scene VO placed at scene offsets + a ducked
  music bed + burned subtitles). Without voiceover, use the music-only
  `assemble.py`.

## Phase 6 — Assemble & VERIFY

Run `scripts/assemble.py` (music-only, 2-chunk) **or** `scripts/assemble_narrated.py`
(voiceover/subtitles). Then **always**:

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
- **Scenes look like a different person than the approved sheet** → your prompt
  described appearance (hair/clothes/age) in words that override the reference. Pass
  the locked reference and describe only the action; remove conflicting descriptors.
- **Too dark from golden-hour light** → "bright even midday daylight."
- **Tail of the movie missing though rc=0** → xfade chain truncation; use more
  chunks and re-verify video==audio.
- **Voiceover sounds like the wrong language** → the TTS model doesn't support it
  (ElevenLabs `multilingual_v2`/`turbo`/`flash` can't do Hebrew). Use `eleven_v3`;
  always confirm with `make_voiceover.py --verify` (whisper).
- **Lip-synced mouth keeps moving after the line** → re-run that `wan2_7` clip with
  "…then closes the mouth and holds a calm closed-mouth smile"; check a back-half frame.
- **Lips don't match the voice** → use the audio EXTRACTED from the wan2_7 clip as
  that scene's VO (don't overlay a separately-timed copy).

Keep the user in the loop, keep characters faithful, and verify every render.
