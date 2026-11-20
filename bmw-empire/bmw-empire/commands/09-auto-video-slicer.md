# 09 — Auto Video Slicer
**الوظيفة:** قص المقاطع من `01_raw_media` حسب `clips_plan.json` بـ FFmpeg وحفظها في `03_sliced_clips`.

```python
from common import *

for c in load("clips_plan.json", []):
    src, out = find_video(c["video_id"]), SL / f"{c['id']}.mp4"
    if not src or out.exists():
        continue
    run(["ffmpeg", "-y", "-loglevel", "error", "-ss", c["start"], "-i", src, "-t", c["end"] - c["start"],
         "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-c:a", "aac", "-b:a", "192k", out])
print("تم القص")
```
