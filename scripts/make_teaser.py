#!/usr/bin/env python3
"""
make_teaser.py — build a short promo teaser (0 generation credits, pure ffmpeg):
title card -> fast HARD-CUT montage of the best clips -> optional finale clip ->
end card, over a music track, trimmed to an EXACT total duration.

Usage:
  make_teaser.py --title title.png --end end.png --music monkeys.mp3 \
                 --clips a.mp4,b.mp4,c.mp4 [--finale everyone_finale.mp4] \
                 [--seconds 20] [--clipsdir video_assets/clips] [--out teaser.mp4]

Notes:
  - Each montage clip is seeked ~2s in (mid-action) and shown for a fixed slice.
  - Hard cuts (concat) hit the target length precisely with zero truncation risk.
  - For a PUBLIC share, prefer Pixar/stylized clips and omit real-photo clips.
"""
import sys, os, subprocess

def arg(flag, default=None):
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else default

TITLE = arg("--title"); END = arg("--end"); MUSIC = arg("--music")
CLIPS = (arg("--clips") or "").split(",") if arg("--clips") else []
FINALE = arg("--finale")
CLIPSDIR = arg("--clipsdir", "video_assets/clips")
SECONDS = float(arg("--seconds", "20"))
OUT = arg("--out", "teaser.mp4")
SEEK = float(arg("--seek", "2.0"))
TITLE_D = float(arg("--title-d", "2.2"))
END_D = float(arg("--end-d", "2.1"))

CLIPS = [c for c in CLIPS if c]
if not (TITLE and END and MUSIC and CLIPS):
    raise SystemExit(__doc__)


def cp(p):
    return p if os.path.isabs(p) or os.path.exists(p) else os.path.join(CLIPSDIR, p)


def main():
    fin_d = 1.7 if FINALE else 0.0
    montage_total = SECONDS - TITLE_D - END_D - fin_d
    if montage_total <= 0:
        raise SystemExit("seconds too small for the cards")
    per = montage_total / len(CLIPS)

    inputs = ["-loop", "1", "-t", f"{TITLE_D}", "-i", TITLE]
    order = [("img", TITLE_D)]
    for c in CLIPS:
        inputs += ["-ss", f"{SEEK}", "-t", f"{per:.3f}", "-i", cp(c)]
        order.append(("vid", per))
    if FINALE:
        inputs += ["-ss", "1.8", "-t", f"{fin_d}", "-i", cp(FINALE)]
        order.append(("vid", fin_d))
    inputs += ["-loop", "1", "-t", f"{END_D}", "-i", END]
    order.append(("img", END_D))
    inputs += ["-i", MUSIC]
    mus_idx = len(order)
    total = sum(d for _, d in order)

    fc = []
    for i, (_, d) in enumerate(order):
        f = (f"[{i}:v]scale=1920:1080:force_original_aspect_ratio=decrease,"
             f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=24,format=yuv420p,"
             f"trim=0:{d:.3f},setpts=PTS-STARTPTS")
        if i == 0:
            f += ",fade=t=in:st=0:d=0.4"
        if i == len(order) - 1:
            f += f",fade=t=out:st={END_D-0.6:.2f}:d=0.6"
        fc.append(f + f"[v{i}]")
    fc.append("".join(f"[v{i}]" for i in range(len(order))) +
              f"concat=n={len(order)}:v=1:a=0[vout]")
    fc.append(f"[{mus_idx}:a]atrim=0:{total:.2f},asetpts=PTS-STARTPTS,afade=t=in:d=0.3,"
              f"afade=t=out:st={total-1.5:.2f}:d=1.5[aout]")
    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(fc),
           "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-crf", "18",
           "-preset", "medium", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
           "-r", "24", "-t", f"{total:.2f}", OUT]
    print(f"{len(order)} segments | {total:.2f}s")
    r = subprocess.run(cmd, capture_output=True, text=True)
    print("rc", r.returncode)
    if r.returncode:
        print(r.stderr[-1500:])
    else:
        print("wrote", OUT)


if __name__ == "__main__":
    main()
