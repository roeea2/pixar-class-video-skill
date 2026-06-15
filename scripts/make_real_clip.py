#!/usr/bin/env python3
"""
make_real_clip.py — turn a real still photo into a ~5s 1920x1080 clip:
a blurred + darkened cover fill behind the sharp, fully-visible photo, then a slow
ffmpeg zoompan. Great as a real-photo interlude right before a recreated scene, or
for an on-real-photos ending.

Usage:
  make_real_clip.py <photo> <out.mp4> [duration_seconds=5.2]

Requires: Pillow, ffmpeg.
"""
import sys, os, subprocess, tempfile
from PIL import Image, ImageFilter, ImageEnhance

W, H = 1920, 1080


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    photo, out = sys.argv[1], sys.argv[2]
    dur = float(sys.argv[3]) if len(sys.argv) > 3 else 5.2

    src = Image.open(photo).convert("RGB")

    # blurred darkened cover fill
    scale = max(W / src.width, H / src.height)
    cover = src.resize((int(src.width * scale), int(src.height * scale)))
    left = (cover.width - W) // 2
    top = (cover.height - H) // 2
    cover = cover.crop((left, top, left + W, top + H))
    cover = cover.filter(ImageFilter.GaussianBlur(40))
    cover = ImageEnhance.Brightness(cover).enhance(0.6)

    # sharp fit centered
    fscale = min(W / src.width, H / src.height)
    fit = src.resize((int(src.width * fscale), int(src.height * fscale)))
    canvas = cover.copy()
    canvas.paste(fit, ((W - fit.width) // 2, (H - fit.height) // 2))

    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
    canvas.save(tmp)

    frames = int(round(dur * 24))
    # slow zoom-in on the static composite
    vf = (f"scale=3840:2160,zoompan=z='min(zoom+0.0008,1.12)':"
          f"d={frames}:s={W}x{H}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)',fps=24,format=yuv420p")
    cmd = ["ffmpeg", "-y", "-loop", "1", "-i", tmp, "-t", f"{dur}",
           "-vf", vf, "-c:v", "libx264", "-crf", "16", "-preset", "medium",
           "-an", "-r", "24", out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    os.unlink(tmp)
    if r.returncode:
        print(r.stderr[-1200:]); raise SystemExit(r.returncode)
    print("wrote", out)


if __name__ == "__main__":
    main()
