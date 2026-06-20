# Voiceover & Lip-Sync (optional)

Use this when the user wants spoken narration — optionally in their **own cloned
voice**, optionally **lip-synced** to a character on screen. All optional: a video
can ship with music + subtitles and no voiceover at all.

## 1. Pick a voice backend

| Backend | Hebrew? | Key needed | Notes |
|---|---|---|---|
| **ElevenLabs `eleven_v3`** | ✅ yes | API key | Best quality; the ONLY ElevenLabs model that speaks Hebrew. Supports **voice cloning**. |
| ElevenLabs `multilingual_v2` / `turbo_v2_5` / `flash_v2_5` | ❌ NO Hebrew | API key | Will mangle Hebrew into Persian/Arabic-sounding gibberish. Do NOT use for Hebrew. |
| **Higgsfield `inworld_text_to_speech`** | ✅ (`Oren (he)`, `Yael (he)`) | none (uses Higgsfield) | Good natural Hebrew, no external key. Preset voices only (no cloning). |
| **macOS `say -v Carmit`** | ✅ | none | Free, offline, but robotic. Fine for a quick draft. |

> ⚠️ **Always verify the TTS actually produced the target language.** TTS models
> silently mispronounce unsupported languages. Transcribe a sample with
> `openai-whisper` and check the detected language (see `make_voiceover.py --verify`).
> This is how we caught `multilingual_v2` emitting Persian instead of Hebrew.

## 2. Clone the user's own voice (ElevenLabs)

- Requires a **paid** ElevenLabs plan (the free tier blocks Instant Voice Cloning).
- Needs a **30–60s clean recording** of the person speaking (any language — it
  clones timbre; the output language comes from the model + text).
- `POST /v1/voices/add` (multipart: `name`, `files=@sample.mp3`) → returns
  `voice_id`. Then generate with `model_id=eleven_v3` and that `voice_id`.
- The sample is uploaded to ElevenLabs — tell the user before doing it.
- Handle the key as a secret: env var only, never write it to a file or commit it.
  Advise rotating it if it was pasted into chat.

## 3. Lip-sync a character to the voice (Wan 2.7)

- **`wan2_7` is the only Higgsfield video model that accepts an `audio` input**
  (`roles: start_image, end_image, audio`). It animates the character's mouth to
  the provided audio. 9:16 / 16:9 / 1:1, 2–15s.
- **Kling 3.0 / 2.6 cannot lip-sync to provided audio** — they only take
  start/end images and a `sound` flag that *invents* their own audio. Do not use
  them to lip-sync a real voice.
- Recipe: upload the per-scene VO (`media_confirm` type `audio`) → `generate_video`
  `model=wan2_7`, `medias=[{role:start_image,...},{role:audio,...}]`, duration ≈ the
  scene length. The output clip embeds the synced audio; **extract that audio back**
  (`ffmpeg -vn`) and use it as the scene's VO so the final mix lines up with the lips
  exactly.
- Gotcha: occasionally the mouth keeps moving after the line ends. Re-run that clip
  with a prompt like *"…then closes the mouth and holds a calm closed-mouth smile;
  mouth stays shut after the sentence."* Verify on a back-half frame.

## 4. Mix the audio

`assemble_narrated.py` places each scene's VO at that scene's start offset and lays a
music **bed** under it at low volume (≈0.12–0.18), with a fade-out tail. Keep VO at
full level; duck the music. Credit royalty-free music on the end card.

Workflow: `make_voiceover.py` (make the lines) → optional `wan2_7` lip-sync →
`assemble_narrated.py` (burn subtitles + mix VO + music).
