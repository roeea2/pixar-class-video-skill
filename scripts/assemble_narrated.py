#!/usr/bin/env python3
"""
assemble_narrated.py — build a narrated reel: each scene = a clip + a burned-in
subtitle + (optional) a voiceover line, hard-cut to a fixed duration, with a music
bed mixed under the voiceover. This is the path to use when the user wants
VOICEOVER and/or per-scene SUBTITLES (vs the crossfaded music-only assemble.py).

Config: a UTF-8 `narration.txt`, one scene per line:
    clip.mp4 | caption text | vo.wav
  - caption may be empty (no subtitle).  vo may be empty (no voiceover).
  - paths are resolved against --clipsdir / --vodir, or absolute.

Usage:
  python3 assemble_narrated.py --scenes narration.txt --music bed.mp3 \
      --size 1080x1920 --seg 5 --clipsdir clips --vodir voiceover --out reel.mp4

Tip: if you lip-synced scenes with wan2_7, set the scene's vo to the audio you
EXTRACTED from the lip-sync clip so the mix lines up with the lips. ALWAYS verify
the final video stream duration == audio stream duration afterwards.
"""
import sys, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
def arg(flag, default=None):
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else default

SCENES = arg("--scenes", "narration.txt")
MUSIC = arg("--music")
SIZE = arg("--size", "1080x1920"); W, H = (int(x) for x in SIZE.lower().split("x"))
SEG = float(arg("--seg", "5"))
CLIPSDIR = arg("--clipsdir", "clips")
VODIR = arg("--vodir", "voiceover")
OUT = arg("--out", "reel.mp4")
TMP = arg("--tmp", "/tmp/narrated_build")
os.makedirs(TMP, exist_ok=True)

def rp(base, p):
    return p if (os.path.isabs(p) or os.path.exists(p)) else os.path.join(base, p)

scenes = []
for line in open(SCENES, encoding="utf-8"):
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    parts = [p.strip() for p in line.split("|")]
    clip = parts[0]
    cap = parts[1] if len(parts) > 1 else ""
    vo = parts[2] if len(parts) > 2 else ""
    scenes.append((clip, cap, vo))
n = len(scenes)
total = SEG * n
print(f"{n} scenes x {SEG}s = {total:.1f}s, {W}x{H}")

# 1) per-scene caption PNGs (reuse make_caption.py)
caps = []
for i, (clip, cap, vo) in enumerate(scenes):
    if cap:
        out = f"{TMP}/cap{i}.png"
        subprocess.run([sys.executable, f"{HERE}/make_caption.py", "--size", SIZE, cap, out],
                       capture_output=True)
        caps.append(out)
    else:
        caps.append(None)

# 2) per-scene video segments (scale/crop to size, burn caption, trim to SEG)
for i, (clip, cap, vo) in enumerate(scenes):
    src = rp(CLIPSDIR, clip)
    seg = f"{TMP}/seg{i}.mp4"
    if caps[i]:
        fc = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
              f"setsar=1,fps=30,trim=0:{SEG},setpts=PTS-STARTPTS[v];"
              f"[1:v]format=rgba,fade=t=in:st=0.25:d=0.4:alpha=1,trim=0:{SEG},setpts=PTS-STARTPTS[c];"
              f"[v][c]overlay=0:0:format=auto,format=yuv420p[o]")
        cmd = ["ffmpeg", "-y", "-i", src, "-loop", "1", "-i", caps[i], "-filter_complex", fc,
               "-map", "[o]"]
    else:
        fc = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
              f"setsar=1,fps=30,trim=0:{SEG},setpts=PTS-STARTPTS,format=yuv420p[o]")
        cmd = ["ffmpeg", "-y", "-i", src, "-filter_complex", fc, "-map", "[o]"]
    cmd += ["-an", "-r", "30", "-t", str(SEG), "-c:v", "libx264", "-crf", "18",
            "-preset", "medium", seg]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(f"seg{i} FAILED"); print(r.stderr[-800:]); sys.exit(1)
print("segments built")

# 3) concat (hard cut) + audio (per-scene VO at offsets + music bed)
inputs = []
for i in range(n):
    inputs += ["-i", f"{TMP}/seg{i}.mp4"]
audio_inputs = []
for i, (clip, cap, vo) in enumerate(scenes):
    if vo:
        audio_inputs.append((i, rp(VODIR, vo)))
for _, path in audio_inputs:
    inputs += ["-i", path]
has_music = bool(MUSIC)
if has_music:
    inputs += ["-i", MUSIC]

fc = ["".join(f"[{i}:v]" for i in range(n)) + f"concat=n={n}:v=1:a=0[vout]"]
amix_labels = []
for k, (scene_i, path) in enumerate(audio_inputs):
    src_idx = n + k
    delay = int(scene_i * SEG * 1000)
    fc.append(f"[{src_idx}:a]aformat=channel_layouts=mono,adelay={delay},volume=1.3[a{k}]")
    amix_labels.append(f"[a{k}]")
have_speech = bool(amix_labels)
if have_speech:
    fc.append("".join(amix_labels) + f"amix=inputs={len(amix_labels)}:duration=longest:normalize=0[sp]")
if has_music:
    mi = n + len(audio_inputs)
    fc.append(f"[{mi}:a]atrim=0:{total},asetpts=PTS-STARTPTS,volume=0.15,"
              f"afade=t=out:st={total-1.5:.2f}:d=1.5[bed]")
# final audio graph
if have_speech and has_music:
    fc.append(f"[sp][bed]amix=inputs=2:duration=longest:normalize=0,atrim=0:{total},"
              f"afade=t=out:st={total-0.6:.2f}:d=0.6[aout]")
elif have_speech:
    fc.append(f"[sp]atrim=0:{total},afade=t=out:st={total-0.6:.2f}:d=0.6[aout]")
elif has_music:
    fc.append(f"[bed]afade=t=out:st={total-0.6:.2f}:d=0.6[aout]")

maps = ["-map", "[vout]"]
if have_speech or has_music:
    maps += ["-map", "[aout]"]
acodec = ["-c:a", "aac", "-b:a", "192k"] if (have_speech or has_music) else []
cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(fc), *maps,
       "-c:v", "libx264", "-crf", "19", "-preset", "medium", *acodec,
       "-movflags", "+faststart", "-r", "30", "-t", str(total), OUT]
r = subprocess.run(cmd, capture_output=True, text=True)
print("final rc", r.returncode)
if r.returncode:
    print(r.stderr[-1500:])
else:
    print(f"wrote {OUT} (~{total:.1f}s) — NOW VERIFY video stream dur == audio stream dur")
