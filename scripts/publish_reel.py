#!/usr/bin/env python3
"""Bot نشر ريلز BMW — يُستدعى من .github/workflows/main.yml.

يقرأ topics.txt من جذر المستودع، يبني الفيديو، وينشر عبر Zernio/Late API.
بدون ZERNIO_KEY وبدون DRY_RUN=1 يُنهي فوراً؛ مع DRY_RUN=1 يبني فقط ولا ينشر."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)  # كل المسارات النسبية (topics.txt, gdrive_vids/...) من جذر المستودع

import os, re, glob, random, datetime, asyncio, sys
import edge_tts, subprocess, requests, imageio_ffmpeg, gdown
from PIL import Image, ImageDraw, ImageFont

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
API = "https://zernio.com" + "/api/v1"
FOLDER_ID = "1KpnN7wch32bfzp5biG3tBJ5PMawWPxTQ"
KEY = os.environ.get("ZERNIO_KEY")
DRY = os.environ.get("DRY_RUN", "0") == "1"

if not KEY and not DRY:
    sys.exit("ZERNIO_KEY غير مضبوط في Settings > Secrets and variables > Actions")
H = {"Authorization": f"Bearer {KEY}"} if KEY else {}
print(f"[start] dry_run={DRY} utc={datetime.datetime.now(datetime.timezone.utc).isoformat()}", flush=True)


def fail(msg):
    sys.exit(f"❌ {msg}")


def api_call(fn, what):
    try:
        r = fn()
    except requests.RequestException as e:
        fail(f"{what}: خطأ اتصال — {e}")
    if r.status_code >= 300:
        fail(f"{what}: HTTP {r.status_code} — {r.text[:300]}")
    try:
        return r.json()
    except ValueError:
        fail(f"{what}: رد غير JSON — {r.text[:300]}")

# ---------- اختيار الموضوع ----------
with open("topics.txt", encoding="utf-8") as fh:
    lines = [ln.strip() for ln in fh if "|" in ln]
if not lines:
    fail("topics.txt فارغ أو لا يحتوي أسطراً تحتوي على |")

now = datetime.datetime.now(datetime.timezone.utc)
slot = 0 if now.hour < 14 else (1 if now.hour < 18 else 2)
idx = (now.timetuple().tm_yday * 3 + slot) % len(lines)
parts = [x.strip() for x in lines[idx].split("|")]
if len(parts) != 3:
    fail(f"سطر topics.txt رقم {idx + 1} يجب أن يحوي 3 أقسام (نص | وصف | وسوم) — وُجد {len(parts)}")
script_text, caption_text, tag_str = parts
tags = [t.strip().lower() for t in tag_str.split(",") if t.strip()]
print(f"[topic] slot={slot} idx={idx} tags={tags}", flush=True)
print(f"[caption] {caption_text}", flush=True)

# ---------- منع التكرار (أفضل جهد — يتخطى بصمت إن لم يتوفر Endpoint) ----------
def already_published():
    try:
        r = requests.get(API + "/posts", headers=H, params={"limit": 50}, timeout=30)
    except requests.RequestException as e:
        print(f"[dedupe] تخطّي الفحص: {e}", flush=True)
        return False
    if r.status_code >= 300:
        print(f"[dedupe] تخطّي الفحص: HTTP {r.status_code}", flush=True)
        return False
    try:
        d = r.json()
    except ValueError:
        print("[dedupe] تخطّي الفحص: رد غير JSON", flush=True)
        return False
    posts = d.get("posts", d) if isinstance(d, dict) else d
    if not isinstance(posts, list):
        return False
    cap = caption_text.strip()
    return any(str(p.get("content") or p.get("caption") or "").strip() == cap
               for p in posts if isinstance(p, dict))


if KEY and already_published():
    if DRY:
        print("[DRY] تنبيه: يوجد منشور بنفس الوصف مسبقاً", flush=True)
    else:
        print("[skip] نفس الوصف منشور مسبقاً — تخطّي هذا التشغيل", flush=True)
        sys.exit(0)

# ---------- بناء الفيديو ----------
os.makedirs("gdrive_vids", exist_ok=True)
try:
    # gdown مثبتة بـ 6.5.2 أعلى: حُذف remaining_ok في v6 (اكتُفي بلا حد 50 ملفاً)
    gdown.download_folder(id=FOLDER_ID, output="gdrive_vids", quiet=True,
                          use_cookies=False, retries=3)
except Exception as e:
    fail(f"تنزيل مجلد Google Drive فشل (تحقق من المشاركة/الحصالة): {e}")

all_vids = []
for ext in ("*.mp4", "*.mov", "*.MP4", "*.MOV"):
    all_vids.extend(glob.glob(f"gdrive_vids/**/{ext}", recursive=True))

matched = [v for v in all_vids if any(t in v.lower() for t in tags)]
others = [v for v in all_vids if v not in matched]
selected = random.sample(matched, min(4, len(matched))) if matched else []
if len(selected) < 4 and others:
    selected.extend(random.sample(others, min(4 - len(selected), len(others))))
if not selected:
    fail(f"لا توجد فيديوهات في المجلد (عدد الملفات {len(all_vids)}) — تحقق من FOLDER_ID")
print("[videos] " + "; ".join(selected), flush=True)

def rights_gate(paths):
    """فحص الحقوق: يقرأ rights_report.json إن وُجد ويمنع عند RIGHTS_ENFORCE=1."""
    report = {}
    rp = ROOT / "rights_report.json"
    if rp.exists():
        try:
            report = json.loads(rp.read_text(encoding="utf-8"))
        except ValueError:
            print("[rights] تعذّر قراءة rights_report.json", flush=True)
    enforce = os.environ.get("RIGHTS_ENFORCE", "0") == "1"
    uncleared = []
    for v in paths:
        stem = Path(v).stem
        entry = report.get(stem)
        status = "معتمد" if (entry and entry.get("cleared")) else ("غير معتمد" if entry else "غير مفحوص")
        print(f"[rights] {stem}: {status}", flush=True)
        if status != "معتمد":
            uncleared.append(stem)
    if uncleared and enforce:
        fail(f"RIGHTS_ENFORCE=1 — مقاطع غير معتمدة: {', '.join(uncleared)}")
    if uncleared:
        print(f"[rights] تحذير: {len(uncleared)} مقطعاً بلا ترخيص موثّق — RIGHTS_ENFORCE=1 ليُمنع النشر", flush=True)


rights_gate(selected)


clip_files = []
for i, vpath in enumerate(selected):
    norm = f"norm_{i}.mp4"
    r = subprocess.run([FFMPEG, "-y", "-i", vpath, "-t", "5.0",
                        "-vf", "scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,fps=30,setsar=1",
                        "-an", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "26",
                        "-pix_fmt", "yuv420p", norm], capture_output=True, text=True)
    if r.returncode != 0:
        fail(f"ffmpeg normalize فشل على {vpath} — {r.stderr[-400:]}")
    clip_files.append(norm)

with open("list.txt", "w") as fh:
    for _ in range(4):
        for c in clip_files:
            fh.write(f"file '{c}'\n")

r = subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", "list.txt",
                    "-c", "copy", "base_vid.mp4"], capture_output=True, text=True)
if r.returncode != 0:
    fail(f"concat الفيديو فشل — {r.stderr[-400:]}")

sentences = [s.strip() for s in re.split(r'(?<=[.!؟،])\s+', script_text) if s.strip()]
if not sentences:
    fail("script_text لا يحتوي جملاً — لا يمكن توليد التعليق الصوتي")
seg_audios, timings = [], []


async def tts_one(text, out):
    for attempt in (1, 2, 3):
        try:
            await edge_tts.Communicate(text, "ar-SA-HamedNeural", rate="-5%").save(out)
            return
        except Exception as e:
            if attempt == 3:
                fail(f"edge-tts فشل بعد 3 محاولات: {e}")
            print(f"[tts] محاولة {attempt} فشلت ({e}) — إعادة بعد 2 ثانية", flush=True)
            await asyncio.sleep(2)


async def build_synced_audio():
    curr_t = 0.0
    for i, sent in enumerate(sentences):
        seg_mp3 = f"seg_{i}.mp3"
        await tts_one(sent, seg_mp3)
        info = subprocess.run([FFMPEG, "-i", seg_mp3], capture_output=True, text=True).stderr
        m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", info)
        if not m:
            print(f"[warn] لم أقرأ مدة seg_{i}.mp3 — افتراض 2.5 ثانية", flush=True)
            dur = 2.5
        else:
            dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))

        words = sent.split()
        chunks = ["  ".join(words[j:j + 4]) for j in range(0, len(words), 4)]
        sub_dur = dur / len(chunks)
        for k, ch in enumerate(chunks):
            timings.append((ch, curr_t + k * sub_dur, curr_t + (k + 1) * sub_dur))

        pad_mp3 = f"pad_{i}.mp3"
        r = subprocess.run([FFMPEG, "-y", "-i", seg_mp3, "-af", "apad=pad_dur=0.35",
                            "-c:a", "libmp3lame", pad_mp3], capture_output=True, text=True)
        if r.returncode != 0:
            fail(f"ffmpeg pad فشل على {seg_mp3} — {r.stderr[-400:]}")
        seg_audios.append(pad_mp3)
        curr_t += dur + 0.35


asyncio.run(build_synced_audio())

with open("aud_list.txt", "w") as fh:
    for a in seg_audios:
        fh.write(f"file '{a}'\n")

r = subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", "aud_list.txt",
                    "-c", "copy", "voice.mp3"], capture_output=True, text=True)
if r.returncode != 0:
    fail(f"concat الصوت فشل — {r.stderr[-400:]}")

def _media_dur(path):
    info = subprocess.run([FFMPEG, "-i", path], capture_output=True, text=True).stderr
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", info)
    return (int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))) if m else 0.0


_vd, _bd = _media_dur("voice.mp3"), _media_dur("base_vid.mp4")
if _vd > _bd:  # نص أطول من الفيديو: نوسّع التكرار بدل قطع الصوت عبر -shortest
    reps = int(4 * _vd / max(_bd, 1.0)) + 1
    with open("list.txt", "w") as fh:
        for _ in range(reps):
            for c in clip_files:
                fh.write(f"file '{c}'\n")
    r = subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", "list.txt",
                        "-c", "copy", "base_vid.mp4"], capture_output=True, text=True)
    if r.returncode != 0:
        fail(f"توسيع base_vid فشل — {r.stderr[-400:]}")
    print(f"[guard] وسّع الفيديو {_bd:.1f}s ← {_vd:.1f}s ليطابق التعليق الصوتي", flush=True)


FONT_FILE = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
if not os.path.exists(FONT_FILE):
    alt = sorted(glob.glob("/usr/share/fonts/**/*.ttf", recursive=True))
    if not alt:
        fail(f"لا يوجد خط {FONT_FILE} ولا أي بديل *.ttf على النظام")
    FONT_FILE = alt[0]
    print(f"[font] استخدام بديل: {FONT_FILE}", flush=True)
font = ImageFont.truetype(FONT_FILE, 40)

sub_files = []
for i, (phrase, st, en) in enumerate(timings):
    img = Image.new("RGBA", (720, 1280), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    x0, y0, x1, y1 = draw.textbbox((360, 910), phrase, font=font, anchor="mm", direction="rtl")
    draw.rounded_rectangle((x0 - 20, y0 - 14, x1 + 20, y1 + 14), radius=16, fill=(0, 15, 35, 225))
    draw.text((360, 910), phrase, font=font, fill=(255, 255, 255, 255), anchor="mm", direction="rtl",
              stroke_width=2, stroke_fill=(0, 0, 0, 255))
    fname = f"sub_{i}.png"
    img.save(fname)
    sub_files.append((fname, st, en))

inputs = ["-y", "-i", "base_vid.mp4", "-i", "voice.mp3"] + [x for f, _, _ in sub_files for x in ("-i", f)]
filters = []
last_v = "0:v"
for i, (_, st, en) in enumerate(sub_files):
    filters.append(f"[{last_v}][{i + 2}:v]overlay=0:0:enable='between(t,{st:.2f},{en:.2f})'[v{i + 1}]")
    last_v = f"v{i + 1}"

def render_final(video_kbps):
    cmd = [FFMPEG] + inputs + ["-filter_complex", ";".join(filters),
           "-map", f"[{last_v}]", "-map", "1:a", "-c:v", "libx264", "-preset", "fast",
           "-b:v", f"{video_kbps}k", "-maxrate", f"{int(video_kbps * 1.3)}k",
           "-bufsize", f"{int(video_kbps * 2)}k", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "96k", "-shortest", "reel.mp4"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        fail(f"دمج reel.mp4 فشل — {r.stderr[-600:]}")
    return Path("reel.mp4").stat().st_size


_bd2 = _media_dur("base_vid.mp4")
_out_s = min(_bd2, _vd) if _vd else _bd2
MAX_MB = float(os.environ.get("MAX_UPLOAD_MB", "15"))
_kb0 = max(300, min(2500, int(MAX_MB * 8192 / max(_out_s, 1.0) - 96)))
_size = render_final(_kb0)
print(f"[ok] reel.mp4 جاهز ({_size // 1048576}MB — {_kb0}k، المدة {_out_s:.1f}s)", flush=True)

# ---------- النشر ----------
if DRY:
    print("[DRY] تم البناء بنجاح — لن يتم النشر. الوصف المخطط:", flush=True)
    print(caption_text, flush=True)
    sys.exit(0)

accs_raw = api_call(lambda: requests.get(API + "/accounts", headers=H, timeout=30), "GET /accounts")
accs = accs_raw.get("accounts", accs_raw) if isinstance(accs_raw, dict) else accs_raw
if not isinstance(accs, list):
    fail(f"شكل رد /accounts غير متوقع: {str(accs_raw)[:200]}")
ig = next((a for a in accs if isinstance(a, dict) and a.get("platform") == "instagram"), None)
ig_id = (ig or {}).get("_id") or (ig or {}).get("id")
if not ig_id:
    fail("لا يوجد حساب إنستغرام مربوط في Zernio")

up_r = None
for _i, _target in enumerate((MAX_MB, MAX_MB / 2, MAX_MB / 4)):
    if _i > 0:  # 413: أعد الترميز بحجم أصغر ثم أعد الرفع
        _kb = max(300, min(2500, int(_target * 8192 / max(_out_s, 1.0) - 96)))
        _size = render_final(_kb)
        print(f"[encode] إعادة ترميز بـ {_kb}k → {_size // 1048576}MB (هدف {_target:.1f}MB)", flush=True)
    with open("reel.mp4", "rb") as fh:
        up_r = requests.post(API + "/media", headers=H,
                             files={"files": ("reel.mp4", fh, "video/mp4")}, timeout=180)
    if up_r.status_code == 413:
        print(f"[upload] HTTP 413 (الحجم {_size // 1048576}MB) — أصغّر وأعيد", flush=True)
        continue
    break
else:
    fail("رفع reel.mp4: HTTP 413 بعد 3 محاولات — تحقق من MAX_UPLOAD_MB")
if up_r.status_code >= 300:
    fail(f"رفع reel.mp4: HTTP {up_r.status_code} — {up_r.text[:300]}")
try:
    up = up_r.json()
except ValueError:
    fail(f"رد /media غير JSON — {up_r.text[:300]}")
files = up.get("files") or up.get("media") or []
candidates = [files] if isinstance(files, dict) else (files if isinstance(files, list) else [])
first = next((c for c in candidates if isinstance(c, dict) and "url" in c), None)
if not first:
    fail(f"رد /media لا يحوي url: {str(up)[:300]}")

body = {
    "content": caption_text,
    "mediaItems": [{"type": "video", "url": first["url"]}],
    "platforms": [{"platform": "instagram", "accountId": ig_id,
                   "platformSpecificData": {"contentType": "reels"}}],
    "publishNow": True,
}
post = api_call(lambda: requests.post(API + "/posts", headers=H, json=body, timeout=120), "نشر /posts")
print("✅ تم النشر بنجاح، المعرف:", post.get("_id") or post.get("id") or post, flush=True)
