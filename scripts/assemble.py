#!/usr/bin/env python3
"""
assemble.py — assemble the class movie from a segment list, using the robust
CHUNKED method (short xfade chains joined together) so the tail never silently
truncates, plus a music ROTATION so the soundtrack never drags.

Layout (default --project video_assets):
  video_assets/
    clips/         *.mp4 segment clips
    titles/        *.png caption/title overlays (+ optional credits.png, blank.png)
    music/         *.mp3 tracks (durations auto-detected; --open picks the opener)
    segments.txt   one "clip.mp4 | caption.png" per line, in playback order

Usage:
  python3 assemble.py --check                 # verify every referenced file exists
  python3 assemble.py                          # render -> movie.mp4
  python3 assemble.py --project DIR --out F.mp4 --open monkeys.mp3 --chunks 2

ALWAYS verify after rendering:
  ffprobe -select_streams v:0 -show_entries stream=duration ... OUT
  ffprobe -select_streams a:0 -show_entries stream=duration ... OUT
  (video and audio durations must match within ~1 frame)
"""
import subprocess, os, sys, math, glob

def arg(flag, default=None):
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else default

PROJECT = arg("--project", "video_assets")
OUT     = arg("--out", "movie.mp4")
OPEN    = arg("--open")                      # e.g. monkeys.mp3
CHUNKS  = arg("--chunks")                    # int override; else auto
TMP     = arg("--tmp", "/tmp/classmovie")
CHECK   = "--check" in sys.argv

C = os.path.join(PROJECT, "clips")
T = os.path.join(PROJECT, "titles")
M = os.path.join(PROJECT, "music")
SEGFILE = os.path.join(PROJECT, "segments.txt")
CRED = os.path.join(T, "credits.png")
os.makedirs(TMP, exist_ok=True)

CRED_D = 6.0; XF = 0.5
SEG = 55.0; XFA = 2.5                         # music rotation window / crossfade


def load_segments():
    segs = []
    with open(SEGFILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            clip, _, cap = line.partition("|")
            segs.append((clip.strip(), cap.strip()))
    return segs


def vd(mp4):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nk=1:nw=1", os.path.join(C, mp4)],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


def adur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nk=1:nw=1", path], capture_output=True, text=True)
    return float(r.stdout.strip())


def build_chunk(slice_segs, include_credits, outpath):
    inputs = []
    for mp4, png in slice_segs:
        inputs += ["-i", os.path.join(C, mp4), "-loop", "1", "-i", os.path.join(T, png)]
    if include_credits:
        inputs += ["-loop", "1", "-t", str(CRED_D), "-i", CRED]
    m = len(slice_segs); fc = []
    for i in range(m):
        vi, oi = 2 * i, 2 * i + 1
        fc.append(f"[{vi}:v]scale=1920:1080:flags=lanczos,setsar=1,fps=24,format=yuv420p[v{i}]")
        fc.append(f"[{oi}:v]format=rgba,fade=t=in:st=0.5:d=0.5:alpha=1,fade=t=out:st=4.2:d=0.5:alpha=1[o{i}]")
        fc.append(f"[v{i}][o{i}]overlay=shortest=1:format=auto,format=yuv420p[s{i}]")
    durs = [vd(mp4) for mp4, _ in slice_segs]; pieces = m
    if include_credits:
        fc.append(f"[{2*m}:v]scale=1920:1080:flags=lanczos,setsar=1,fps=24,format=yuv420p,"
                  f"fade=t=out:st={CRED_D-1}:d=1[s{m}]")
        durs += [CRED_D]; pieces = m + 1
    cur = "s0"; offset = 0.0
    for i in range(1, pieces):
        offset += durs[i-1] - XF
        out = f"x{i}" if i < pieces - 1 else "vout"
        fc.append(f"[{cur}][s{i}]xfade=transition=fade:duration={XF}:offset={offset:.4f}[{out}]")
        cur = out
    chunk_len = sum(durs) - XF * (pieces - 1)
    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", "[vout]",
           "-c:v", "libx264", "-crf", "14", "-preset", "medium", "-r", "24", "-an", outpath]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(f"  {os.path.basename(outpath)}: {len(slice_segs)} segs, rc {r.returncode}, len {chunk_len:.2f}")
    if r.returncode:
        print(r.stderr[-1500:])
    return chunk_len


def main():
    segs = load_segments()

    if CHECK:
        missing = []
        for mp4, png in segs:
            if not os.path.exists(os.path.join(C, mp4)): missing.append(mp4)
            if png and not os.path.exists(os.path.join(T, png)): missing.append(png)
        if not glob.glob(os.path.join(M, "*.mp3")): missing.append("music/*.mp3")
        print("segments:", len(segs)); print("MISSING:", missing or "none")
        sys.exit(1 if missing else 0)

    n = len(segs)
    nch = int(CHUNKS) if CHUNKS else max(1, math.ceil(n / 45))
    bounds = [round(n * k / nch) for k in range(nch + 1)]
    print(f"{n} segments -> {nch} chunk(s) at {bounds}")
    lens = []
    for k in range(nch):
        a, b = bounds[k], bounds[k+1]
        last = (k == nch - 1)
        lens.append(build_chunk(segs[a:b], last, os.path.join(TMP, f"chunk{k}.mp4")))
    total = sum(lens) - XF * (nch - 1)
    print("chunk lens", [f"{x:.2f}" for x in lens], "total", f"{total:.2f}")

    # discover music; opener first
    tracks = sorted(glob.glob(os.path.join(M, "*.mp3")))
    if OPEN:
        op = [t for t in tracks if os.path.basename(t) == OPEN]
        tracks = op + [t for t in tracks if os.path.basename(t) != OPEN]
    if not tracks:
        raise SystemExit("no music tracks in " + M)
    tdur = {t: adur(t) for t in tracks}

    # rotation plan
    plan = []; covered = 0.0; ti = 0; reps = {}
    while covered < total + 4:
        t = tracks[ti % len(tracks)]; r = reps.get(t, 0)
        st = round((r * 63.0) % max(1.0, tdur[t] - SEG - 1.0), 2)
        plan.append((t, st)); reps[t] = r + 1
        covered += SEG if len(plan) == 1 else SEG - XFA
        ti += 1

    # join chunks (xfade) + lay rotated audio
    inputs = []
    for k in range(nch):
        inputs += ["-i", os.path.join(TMP, f"chunk{k}.mp4")]
    for t, _ in plan:
        inputs += ["-i", t]
    fc = []
    cur = "0:v"; off = 0.0
    for k in range(1, nch):
        off += lens[k-1] - XF
        out = f"vx{k}" if k < nch - 1 else "vout"
        fc.append(f"[{cur}][{k}:v]xfade=transition=fade:duration={XF}:offset={off:.4f}[{out}]")
        cur = out
    if nch == 1:
        fc.append("[0:v]copy[vout]")
    base = nch
    for j, (t, st) in enumerate(plan):
        fc.append(f"[{base+j}:a]atrim={st:.2f}:{st+SEG:.2f},asetpts=PTS-STARTPTS[ma{j}]")
    fc.append("[ma0]afade=t=in:d=0.8[mc0]"); cur = "mc0"
    for j in range(1, len(plan)):
        fc.append(f"[{cur}][ma{j}]acrossfade=d={XFA}[mc{j}]"); cur = f"mc{j}"
    fc.append(f"[{cur}]atrim=0:{total:.2f},afade=t=out:st={total-3:.2f}:d=3,volume=0.9[aout]")
    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(fc),
           "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-crf", "18",
           "-preset", "medium", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
           "-r", "24", OUT]
    print("rotation:", " -> ".join(f"{os.path.basename(t).split('.')[0]}@{int(s)}" for t, s in plan))
    r = subprocess.run(cmd, capture_output=True, text=True)
    print("join rc", r.returncode)
    if r.returncode:
        print(r.stderr[-1500:]); return
    print(f"wrote {OUT}  (~{total:.1f}s)  — NOW VERIFY video==audio duration!")


if __name__ == "__main__":
    main()
