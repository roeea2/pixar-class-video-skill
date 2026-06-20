#!/usr/bin/env python3
"""
make_voiceover.py — generate per-scene voiceover WAVs (one per line).

Backends:
  say         macOS built-in TTS (free, offline). e.g. Hebrew voice "Carmit".
  elevenlabs  ElevenLabs API. For Hebrew you MUST use model eleven_v3
              (multilingual_v2/turbo/flash do NOT speak Hebrew). Supports cloning.
  (Higgsfield Inworld TTS — voices "Oren (he)"/"Yael (he)" — is great and needs no
   external key, but it's an MCP tool, not callable from this script. Use the
   generate_audio tool directly for that backend.)

Lines: a UTF-8 file, one spoken line per scene (blank lines skipped).

Usage:
  # macOS Carmit:
  make_voiceover.py --backend say --voice Carmit --lines lines.txt --out voiceover/

  # ElevenLabs with a preset voice (env ELEVENLABS_API_KEY):
  make_voiceover.py --backend elevenlabs --voice <voice_id> --lines lines.txt --out voiceover/

  # ElevenLabs cloning the user's voice from a sample (paid plan required):
  make_voiceover.py --backend elevenlabs --clone /path/sample.mp3 --lines lines.txt --out voiceover/

  add --verify to transcribe each WAV with openai-whisper and print the detected language.
"""
import sys, os, subprocess, json, urllib.request

def arg(flag, default=None):
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else default

BACKEND = arg("--backend", "say")
VOICE = arg("--voice")
CLONE = arg("--clone")
MODEL = arg("--model", "eleven_v3")
LINES = arg("--lines")
OUT = arg("--out", "voiceover")
RATE = arg("--rate", "172")
VERIFY = "--verify" in sys.argv

if not LINES:
    raise SystemExit(__doc__)
os.makedirs(OUT, exist_ok=True)
lines = [l.strip() for l in open(LINES, encoding="utf-8") if l.strip()]


def to_wav(src, wav):
    subprocess.run(["ffmpeg", "-y", "-i", src, "-ar", "48000", "-ac", "1", wav],
                   capture_output=True)


def gen_say(i, txt, wav):
    aiff = wav.replace(".wav", ".aiff")
    subprocess.run(["say", "-v", VOICE or "Carmit", "-r", RATE, "-o", aiff, txt], check=True)
    to_wav(aiff, wav); os.path.exists(aiff) and os.remove(aiff)


def el_key():
    k = os.environ.get("ELEVENLABS_API_KEY")
    if not k:
        raise SystemExit("set ELEVENLABS_API_KEY for the elevenlabs backend")
    return k


def el_clone(sample):
    import requests  # optional; fall back to curl-style if missing
    key = el_key()
    boundary = "----vo"
    with open(sample, "rb") as f:
        data = f.read()
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"name\"\r\n\r\nClone\r\n"
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"files\"; filename=\"s.mp3\"\r\n"
            f"Content-Type: audio/mpeg\r\n\r\n").encode() + data + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request("https://api.elevenlabs.io/v1/voices/add", data=body,
        headers={"xi-api-key": key, "Content-Type": f"multipart/form-data; boundary={boundary}"})
    vid = json.load(urllib.request.urlopen(req))["voice_id"]
    print("cloned voice_id:", vid); return vid


def gen_eleven(voice_id, txt, wav):
    key = el_key()
    body = json.dumps({"text": txt, "model_id": MODEL}).encode()
    req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        data=body, headers={"xi-api-key": key, "Content-Type": "application/json"})
    mp3 = wav.replace(".wav", ".mp3")
    with urllib.request.urlopen(req) as r:
        open(mp3, "wb").write(r.read())
    to_wav(mp3, wav)


voice_id = VOICE
if BACKEND == "elevenlabs" and CLONE:
    voice_id = el_clone(CLONE)

total = 0.0
for i, txt in enumerate(lines, 1):
    wav = os.path.join(OUT, f"vo{i}.wav")
    if BACKEND == "say":
        gen_say(i, txt, wav)
    elif BACKEND == "elevenlabs":
        if not voice_id:
            raise SystemExit("elevenlabs needs --voice <id> or --clone <sample>")
        gen_eleven(voice_id, txt, wav)
    else:
        raise SystemExit("unknown backend: " + BACKEND)
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nk=1:nw=1", wav], capture_output=True, text=True).stdout or 0)
    total += d
    print(f"vo{i}  {d:5.2f}s  {txt}")
print(f"total {total:.2f}s -> {OUT}")

if VERIFY:
    try:
        import whisper, warnings
        warnings.filterwarnings("ignore")
        m = whisper.load_model("small")
        print("--- language verification (whisper) ---")
        for i in range(1, len(lines) + 1):
            wav = os.path.join(OUT, f"vo{i}.wav")
            a = whisper.pad_or_trim(whisper.load_audio(wav))
            mel = whisper.log_mel_spectrogram(a, n_mels=m.dims.n_mels).to(m.device)
            _, p = m.detect_language(mel)
            print(f"  vo{i}: detected={max(p, key=p.get)}  (verify it matches the intended language!)")
    except ImportError:
        print("(install openai-whisper to use --verify)")
