```python
import subprocess
from common import *

VIDEOS = [
    ("bmw_m5_v10", "0x003366"),
    ("bmw_m3_e30", "0x00A0E9"),
    ("bmw_m4_csl", "0xE2001A"),
]

for vid_id, color in VIDEOS:
    vid_path = RAW / f"{vid_id}.mp4"
    if not vid_path.exists():
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c={color}:s=1080x1920:d=25:r=25",
            "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
            "-t", "25",
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            str(vid_path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print("FFMPEG ERROR:", res.stderr)
            raise SystemExit(1)
        print(f"✅ تم توليد: {vid_path.name}")

print("تم. الملفات في 01_raw_media")
```
