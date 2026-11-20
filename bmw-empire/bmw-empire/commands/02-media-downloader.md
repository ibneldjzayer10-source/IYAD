```python
import subprocess
from common import *

# توليد فيديوهات أساسية عالية الجودة محلياً بألوان BMW M دون الاعتماد على أي موقع خارجي
VIDEOS = [
    ("bmw_m5_v10", "BMW M5 E60 V10 - 507 HP", "0x003366"),
    ("bmw_m3_e30", "BMW M3 E30 LEGEND", "0x00A0E9"),
    ("bmw_m4_csl", "BMW M4 CSL - 550 HP", "0xE2001A"),
]

for vid_id, title, color in VIDEOS:
    vid_path = RAW / f"{vid_id}.mp4"
    if not vid_path.exists():
        # توليد فيديو MP4 احترافي مدته 30 ثانية مع حركة بصرية ونبض إيقاعي
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c={color}:s=1920x1080:d=30:r=25",
            "-f", "lavfi", "-i", "sine=frequency=65:duration=30",
            "-vf", "geq=r='r(X,Y)+30*sin(T*2+X/100)':g='g(X,Y)+20*cos(T*2+Y/100)':b='b(X,Y)+40*sin(T)'",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-shortest",
            str(vid_path)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"✅ تم توليد الفيديو الأساسي: {vid_path.name}")

print("تم. الملفات في 01_raw_media")
```
