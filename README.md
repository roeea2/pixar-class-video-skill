<div align="center">

<pre>
██████╗  ██████╗ ███████╗███████╗ █████╗ ██╗
██╔══██╗██╔═══██╗██╔════╝██╔════╝██╔══██╗██║
██████╔╝██║   ██║█████╗  █████╗  ███████║██║
██╔══██╗██║   ██║██╔══╝  ██╔══╝  ██╔══██║██║
██║  ██║╚██████╔╝███████╗███████╗██║  ██║██║
╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═╝╚═╝
</pre>

# 🎬 Pixar Class Video — a step-by-step skill

**Turn a class of kids' photos + hobbies into a beautiful Pixar-style end-of-year movie.**
Every child becomes a faithful 3D character, with animated hobby scenes, Hebrew/RTL
title cards, real-photo interludes, a rotating soundtrack, a whole-class finale, and a teaser for parents.

🇮🇱 [עברית / Hebrew README](README.he.md)

<img src="assets/images/teaser.gif" width="640" alt="Teaser preview (Pixar montage)" />

</div>

---

## ✨ What it is

A [Claude Code](https://claude.com/claude-code) **skill** that acts as your *director*.
It walks you **step by step** — asking what to do at each phase instead of guessing — and
drives the [Higgsfield](https://higgsfield.ai) MCP (image + video generation) plus `ffmpeg`
to produce a polished ~7–10 minute film.

It encodes everything learned from building a real class movie: how to make characters
**actually look like the kids**, the prompt traps to avoid, RTL Hebrew title cards, a
soundtrack that never drags, and an assembly method that won't silently drop your ending.

Optional extras you can switch on: **voiceover** (text-to-speech, or the user's own
**cloned voice**), **lip-sync** so an on-camera character mouths the words, and
**per-scene subtitles / text-over** — all RTL-aware.

<div align="center">
<img src="assets/images/still_class.jpg" width="32%" alt="Whole-class finale" />
<img src="assets/images/still_concert.jpg" width="32%" alt="Teacher concert scene" />
<img src="assets/images/still_guitar.jpg" width="32%" alt="A pupil's hobby scene" />
</div>

## 🧭 How the wizard works

| Phase | What happens (you approve each step) |
|------:|--------------------------------------|
| **0. Setup & scope** | Check tools, create the workspace, ask language / length / music / scenes-per-kid. |
| **1. Roster** | You provide each child's name, face photo, and 1–3 hobbies. |
| **2. Per-child** | Crop → **character sheet** → *"does this look like them?"* → hobby scenes → animate. |
| **3. Cards & subtitles** | Hebrew/RTL title cards + optional per-scene text-over (digit/`?` glyph traps handled). |
| **4. Groups & real photos** | Whole-class finale, event recreations, real-photo interludes. |
| **5. Audio** | Music (always) + **optional voiceover** (TTS / cloned voice) + **optional lip-sync**. |
| **6. Assemble & verify** | Chunked or narrated render, then **verify video length == audio length**. |
| **7. Teaser** | Optional 15–20s promo for parents (0 generation credits). |

## 🚀 Install (as a Claude Code skill)

```bash
git clone https://github.com/roeea2/pixar-class-video-skill.git \
  ~/.claude/skills/pixar-class-video
```

Then in Claude Code just say *"make a Pixar end-of-year class video"* or run `/pixar-class-video`.

> You can also drop the folder into a project's `.claude/skills/` for project-local use.

## 🧰 Requirements

- **Claude Code** with the **Higgsfield MCP** connected (image/video generation + credits).
- `ffmpeg` + `ffprobe` on PATH.
- `python3` with **Pillow** (`pip install pillow`) for the title cards.
- A Hebrew-capable font for RTL cards (macOS ships *SF Hebrew Rounded*).

## 📦 What's inside

```
SKILL.md                     the guided wizard (read first)
references/
  likeness-recipe.md         make characters resemble the real kids
  prompt-gotchas.md          NSFW false-flags, crowd fillers, eye color, ...
  higgsfield-pipeline.md     exact MCP tools / models / params / polling
  hebrew-titles.md           RTL cards with PIL (the digit & "?" traps)
  assembly-and-music.md      chunked ffmpeg assembler + music rotation + the truncation bug
  subtitles-and-captions.md  per-scene subtitles / text-over (lower-third, RTL)
  voiceover-and-lipsync.md   optional TTS / voice cloning / wan2_7 lip-sync + audio mixing
scripts/
  make_title_card.py         Hebrew/RTL title, caption & blank cards
  make_caption.py            per-scene subtitle / text-over overlay (RTL, auto-fit)
  make_real_clip.py          real photo -> Ken-Burns clip
  make_voiceover.py          per-scene voiceover (say / ElevenLabs clone) + --verify
  assemble.py                build the movie (chunked, music-only) — then VERIFY
  assemble_narrated.py       build with voiceover + burned subtitles + music bed
  make_teaser.py             build the promo teaser (pure ffmpeg)
```

## 🔑 The hard-won lessons (so your film comes out great)

- **Likeness first** — state the real age, face shape, exact hair/eye color; demand *"only mild stylization."* Approve each sheet before building scenes.
- **Let the reference define the look** — once a sheet is locked, pass it to every scene and describe only the *action*; restating hair/clothes/age in the prompt silently produces a different-looking person.
- **One approval gate per artifact** — look → each scene → animation → voice → lip-sync → assembly. An OK on a cheap still saves re-rolling every expensive clip after it.
- **Ask for keys up front** — if voiceover needs an ElevenLabs key, request it before starting; keep it out of the repo and rotate it after.
- **One child per solo scene** — or the model duplicates them.
- **Verify every render** — a deep `xfade` chain can silently truncate the tail (rc=0!). Always compare the **video** stream duration to the **audio** stream duration.
- **Crowds** — drop the word *"diverse"*; state the class's real look, or you get random mismatched fillers.
- **Music rotation** — cycle a few tracks every ~55s so a long film never drags.

## 🔒 Privacy

These films feature **real children**. The skill never uploads photos anywhere except the
generation API you choose, and it warns before placing real faces on any shared surface.
The preview above is **stylized Pixar artwork only** — no real photographs are included in
this repo. Keep the finished film within your class community.

## 🙏 Credits

Built with [Claude Code](https://claude.com/claude-code), the [Higgsfield](https://higgsfield.ai)
MCP, and `ffmpeg`. Music in the reference workflow: *Kevin MacLeod* (incompetech.com), CC-BY 4.0.

Crafted by **RoeeAI**. Licensed under [MIT](LICENSE).
