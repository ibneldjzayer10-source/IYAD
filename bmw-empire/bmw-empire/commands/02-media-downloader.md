```python
import urllib.request
from common import *

# روابط مباشرة لفيديوهات سيارات BMW عالية الجودة لا تحظرها السيرفرات
DIRECT_BMW_VIDEOS = [
    ("bmw_m4_track", "https://pexels.com"),
    ("bmw_night_drive", "https://pexels.com"),
]

for vid_id, url in DIRECT_BMW_VIDEOS:
    out_file = RAW / f"{vid_id}.mp4"
    if not out_file.exists():
        print(f"⬇️ جاري تحميل: {vid_id}...")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as resp, open(out_file, "wb") as f:
            f.write(resp.read())
        print(f"✅ تم تحميل: {out_file.name}")

print("تم. الملفات في 01_raw_media")
```
