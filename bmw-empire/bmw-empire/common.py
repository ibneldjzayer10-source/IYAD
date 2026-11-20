import json, os, re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW, TR, SL, FIN, PUB, ASSETS = (ROOT / n for n in
    ["01_raw_media", "02_transcripts", "03_sliced_clips", "04_final_reels", "05_published", "assets"])
for _d in (RAW, TR, SL, FIN, PUB, ASSETS):
    _d.mkdir(exist_ok=True)

BRAND = {"light_blue": "#00A0E9", "dark_blue": "#003366", "red": "#E2001A"}


def load_env():
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_env()
LANG = os.environ.get("REEL_LANG", "ar")  # ar | en


def load(name, default=None):
    p = ROOT / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def save(name, obj):
    (ROOT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def run(cmd, **kw):
    cmd = [str(c) for c in cmd]
    print("$", " ".join(cmd)[:220])
    return subprocess.run(cmd, check=True, **kw)


def duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def approved_ids():
    """مصادر وافقت عليها يدوياً (روابط/معرفات) في approved_urls.txt"""
    p, ids = ROOT / "approved_urls.txt", set()
    if p.exists():
        for tok in p.read_text(encoding="utf-8").split():
            m = re.search(r"(?:v=|youtu\.be/|shorts/)([\w-]{11})", tok)
            ids.add(m.group(1) if m else tok.strip())
    return ids


def cleared_ids():
    r = load("rights_report.json", {})
    return {k for k, v in r.items() if v.get("cleared")}


def find_video(vid):
    for p in RAW.glob(f"{vid}.*"):
        if p.suffix.lower() in (".mp4", ".mkv", ".webm", ".mov"):
            return p
