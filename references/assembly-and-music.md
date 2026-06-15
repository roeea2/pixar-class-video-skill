# Assembly & Music

How clips + cards + music become the final movie — and the bug that will bite you.

## ⚠️ The silent xfade-truncation bug (read this)

Chaining many `xfade` crossfades in a single ffmpeg filtergraph **silently drops
the tail** once the chain gets deep (~80+ segments): the video stream ends seconds
before the audio, ffmpeg returns **rc=0 with no error**, and the container
duration still looks right. You only catch it by comparing the **video stream**
duration to the **audio stream** duration.

**Always verify:**
```
ffprobe -v error -select_streams v:0 -show_entries stream=duration,nb_frames -of default=nk=1:nw=1 OUT.mp4
ffprobe -v error -select_streams a:0 -show_entries stream=duration            -of default=nk=1:nw=1 OUT.mp4
```
They must match within ~1 frame.

## The fix: chunked assembly

`scripts/assemble.py` renders the movie as a few **shorter** xfade chains
(chunks), each its own video-only file, then joins the chunks with a single xfade
and lays the audio. Short chains don't truncate. If your movie grows past what 2
chunks handle, add a 3rd. Defaults: per-chunk `crf 14` video-only, final `crf 18`
+ AAC 192k, 24 fps, `+faststart`.

Each segment is: scale to 1920×1080, `setsar=1`, `fps=24`, then a looped caption
PNG overlaid with alpha fades (in ~0.5s, out near the end), crossfaded into the
next at `XF=0.5s`. Durations are read **exactly** per clip with ffprobe (`vd()`),
never assumed.

## Music rotation (so it never drags)

Instead of one long track, the assembler **rotates** a small set of royalty-free
tracks every ~55s (`SEG=55`, `XFA=2.5s` acrossfade), opening with a chosen
favorite and pulling a different section of each track on reuse, then trims to the
exact total and adds a 3s fade-out. This keeps a 7–10 min film from feeling
repetitive. Tracks live in `video_assets/music/`; credit them on the end card
(e.g. Kevin MacLeod, CC-BY 4.0).

## The segment list

`assemble.py` holds a `segs` list of `(clip.mp4, caption.png)` tuples in playback
order — intro, then per child (`hero`, hobby scenes), then events/groups (each
optionally preceded by a real-photo clip), the whole-class finale, real-photo
ending, and a credits card. Editing one child = swap their tuples; re-run.

Run:
```
python3 scripts/assemble.py --check   # validate every file exists
python3 scripts/assemble.py           # render, then VERIFY durations
```

## Real-photo interludes

`scripts/make_real_clip.py` turns a still photo into a ~5s clip: a blurred,
darkened cover fill + the sharp photo fit on top, then a slow ffmpeg `zoompan`.
Reuse the matching scene's caption card. Great right before each recreated scene
and for an on-real-photos ending.
