# 14 — Audio Mixer
**الوظيفة:** يمزج التعليق الصوتي + صوت المحرك الأصلي + موسيقى (من `assets/music/*.mp3`، ضع موسيقى مرخّصة/بلا حقوق) مع خفض الموسيقى تلقائياً عند الكلام (sidechain). مدة الناتج = max(مدة الفيديو، التعليق+0.6ث) مع تكرار الفيديو عند الحاجة.
**المخرجات:** `03_sliced_clips/<id>_m.mp4`

```python
from common import *

music = sorted((ASSETS / "music").glob("*.mp3"))
for n, c in enumerate(load("clips_plan.json", [])):
    vid, vo, out = SL / f"{c['id']}_b.mp4", SL / f"{c['id']}_vo.mp3", SL / f"{c['id']}_m.mp4"
    if not vid.exists() or not vo.exists() or out.exists():
        continue
    T = max(duration(vid), duration(vo) + 0.6)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-stream_loop", "-1", "-i", vid, "-i", vo]
    if music:
        cmd += ["-stream_loop", "-1", "-i", music[n % len(music)]]
        fc = ("[0:a]volume=0.35[o];[1:a]volume=1.3,asplit=2[vo][sc];[2:a]volume=0.5[m0];"
              "[m0][sc]sidechaincompress=threshold=0.05:ratio=8:attack=20:release=400[m];"
              "[o][m][vo]amix=inputs=3:duration=longest:normalize=0,alimiter=limit=0.95[a]")
    else:
        fc = ("[0:a]volume=0.35[o];[1:a]volume=1.3[vo];"
              "[o][vo]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95[a]")
    cmd += ["-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-t", f"{T:.2f}",
            "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-c:a", "aac", "-b:a", "192k", out]
    run(cmd)
print("تم المزج")
```
