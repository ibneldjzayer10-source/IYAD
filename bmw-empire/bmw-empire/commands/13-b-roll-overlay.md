# 13 — B-Roll Overlay
**الوظيفة:** يدمج صوراً/مخططات هندسية من `assets/` أثناء الشرح. يبحث أولاً عن `assets/<رمز المحرك>.png|jpg` (مثل `S58.png`)، ثم عن أي صورة في `assets/broll/`. استخدم صوراً تملكها أو مرخّصة. بدون صور يُنسخ الفيديو كما هو.
**المخرجات:** `03_sliced_clips/<id>_b.mp4`

```python
import shutil
from common import *

EXT = ("*.png", "*.jpg", "*.jpeg")


def pick(code):
    if code:
        for e in EXT:
            m = sorted(ASSETS.glob(code + e[1:]))
            if m:
                return m[0]
    pool = [p for e in EXT for p in sorted((ASSETS / "broll").glob(e))]
    return pool[0] if pool else None


for c in load("clips_plan.json", []):
    src, out = SL / f"{c['id']}_s.mp4", SL / f"{c['id']}_b.mp4"
    if not src.exists() or out.exists():
        continue
    img = pick(c.get("engine"))
    if not img:
        shutil.copy(src, out)
        continue
    d = duration(src)
    t1, t2 = d * 0.25, d * 0.60
    fc = ("[1:v]scale=900:-1,format=rgba[i];"
          f"[0:v][i]overlay=(W-w)/2:260:shortest=1:enable='between(t,{t1:.2f},{t1 + 3:.2f})+between(t,{t2:.2f},{t2 + 3:.2f})'[v]")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-loop", "1", "-i", img, "-filter_complex", fc,
         "-map", "[v]", "-map", "0:a?", "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-c:a", "copy", out])
print("تم دمج الـ B-Roll")
```
