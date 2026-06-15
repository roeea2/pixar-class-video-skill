# Higgsfield MCP Pipeline

Exact tools, models, and params for image/video generation.

## Upload a local image (to use as a reference)

1. `media_upload` with the filename → returns `{ media_id, upload_url }`.
2. `PUT` the raw bytes to `upload_url` (e.g. `curl -X PUT --upload-file f.png "<url>"`),
   expect HTTP 200.
3. `media_confirm` with the `media_id` → returns `{ media_id, status: "uploaded" }`.

The confirmed `media_id` is then usable in `medias[].value`. **Never** pass an
`https://` URL in `medias[].value` — only a `media_id` (from upload/import) or a
prior `job_id`. For web URLs, use `media_import_url` first.

## Generate an image (character sheets & scenes)

`generate_image`:
- `model: "nano_banana_pro"` (routes to nano_banana_2)
- `aspect_ratio: "16:9"`, `resolution: "2k"`
- `prompt`: built per `likeness-recipe.md` / `prompt-gotchas.md`
- `medias: [{ role: "image", value: "<media_id or job_id>" }, ...]` — seed the
  approved character sheet(s) + face crop(s). ≥4 refs are fine.
- Optionally `count` up to 4 for variations.

## Animate a still into a clip

`generate_video`:
- `model: "kling3_0"`, `duration: 5`
- `medias: [{ role: "start_image", value: "<image job_id>" }]`
- `prompt`: describe gentle, natural motion (the clip is video-only in assembly;
  the soundtrack is added later, so on-clip sound doesn't matter).
- Other identity-preserving option: `seedance_2_0`. Default to `kling3_0` here.

## Poll for results

`job_status`:
- arg is **`jobId`** (a UUID), plus `sync: true` to block ~25s until terminal.
- Image ≈ 10–20s; video ≈ 60–180s. If non-terminal, it returns
  `poll_after_seconds` — wait, then call again. Completed jobs return a
  `results.rawUrl` (download with curl).

## Money / housekeeping

- `balance` shows remaining credits. Don't warn the user unless it's genuinely low.
- Downloads: `curl -s -o out.png "<rawUrl>"`.
- Keep a stable id map (which `media_id`/`job_id` is which character) — you reuse
  the approved sheet across all of that kid's scenes.

## Tips

- The MCP tool schemas may be **deferred** — load a tool's schema before first use.
- Standard clip length here is ~5.04s; the assembler reads exact per-clip
  durations with ffprobe rather than assuming.
