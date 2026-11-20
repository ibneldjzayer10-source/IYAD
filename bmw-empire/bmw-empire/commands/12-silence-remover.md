# 12-silence-remover
**الوظيفة:** يكتشف فترات الصمت (`silencedetect`) ويقصّها من الفيديو والصوت معاً لتسريع الإيقاع. إن لم يوجد صمت يُنسخ الملف كما هو.
**المخرجات:** `03_sliced_clips/<id>_s.mp4`

```python
import re, shutil, subprocess
from common import *

NOISE, MIN_SIL, PAD, MAX_SEGS = "-35dB", 0.45, 0.08, 60

for c in load("clips_plan.json", []):
    src, out = SL / f"{c['id']}_v.mp4", SL / f"{c['id']}_s.mp4"
    if not src.exists() or out.exists():
        continue
    dur = duration(src)
    r = subprocess.run(["ffmpeg", "-i", str(src), "-af", f"silencedetect=noise={NOISE}:d={MIN_SIL}",
                        "-f", "null", "-"], capture_output=True, text=True)
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: (-?[\d.]+)", r.stderr)]
    if len(ends) < len(starts):
        ends.append(dur)
    keep, prev = [], 0.0
    for s, e in zip(starts, ends):
        a, b = max(0, prev - PAD), min(dur, max(s, 0) + PAD)
        if b - a > 0.2:
            keep.append((a, b))
        prev = e
    if dur - prev > 0.2:
        keep.append((max(0, prev - PAD), dur))
    total = sum(b - a for a, b in keep)
    if not starts or len(keep) > MAX_SEGS or total < 8:
        shutil.copy(src, out)
        continue
    expr = "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in keep)
    fs = SL / f"{c['id']}.filt"
    fs.write_text(f"[0:v]select='{expr}',setpts=N/FRAME_RATE/TB[v];[0:a]aselect='{expr}',asetpts=N/SR/TB[a]",
                  encoding="utf-8")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-filter_complex_script", fs, "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-c:a", "aac", out])
    print(f"{c['id']}: {dur:.1f}s → {total:.1f}s")
```
