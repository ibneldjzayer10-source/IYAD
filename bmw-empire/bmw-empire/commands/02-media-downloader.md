```python
import subprocess, urllib.request
from common import *

# تحميل صور وفيديوهات BMW من خوادم Wikimedia المفتوحة (لا تحظر السيرفرات أبداً)
WIKI_ASSETS = [
    ("bmw_m3_e30", "https://wikimedia.org"),
    ("bmw_m4_gts", "https://wikimedia.org"),
    ("bmw_m5_f90", "https://wikimedia.org"),
    ("bmw_engine_v10", "https://wikimedia.org"),
]

headers = {"User-Agent": "BMW-Documentary-Bot/1.0 (https://github.com)"}

for name, url in WIKI_ASSETS:
    img_path = ASSETS / f"{name}.jpg"
    vid_path = RAW / f"{name}.mp4"
    if not img_path.exists():
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as r, open(img_path, "wb") as f:
            f.write(r.read())
    if not vid_path.exists():
        # تحويل كل صورة عالية الدقة إلى فيديو سينمائي متحرك (Zoom-in) مدته 30 ثانية
        subprocess.run([
            "ffmpeg", "-y", "-loop", "1", "-i", str(img_path),
            "-vf", "scale=1920:1080,zoompan=z='min(zoom+0.001,1.3)':d=750:s=1920x1080:fps=25",
            "-t", "30", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(vid_path)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"✅ تم تجهيز فيديو: {vid_path.name}")

print("تم. الملفات في 01_raw_media")
```
