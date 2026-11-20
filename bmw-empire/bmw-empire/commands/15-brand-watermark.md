# 15 — Brand Watermark + Captions + Export
**الوظيفة:** يحرق الترجمة (ASS) ويضع شعار الحساب شفافاً أعلى اليمين ويصدّر الفيديو النهائي إلى `04_final_reels`. إن لم يوجد `assets/logo.png` يُولَّد شعار نصي بألوان BMW M من `ACCOUNT_HANDLE`.

```python
import os
from PIL import Image, ImageDraw, ImageFont
from common import *

HANDLE = os.environ.get("ACCOUNT_HANDLE", "@BMW_M_FANS")
logo = ASSETS / "logo.png"
if not logo.exists():
    fonts = sorted((ASSETS / "fonts").glob("*.ttf"))
    try:
        font = ImageFont.truetype(str(fonts[0]) if fonts else "DejaVuSans-Bold.ttf", 56)
    except OSError:
        font = ImageFont.load_default()
    im = Image.new("RGBA", (620, 110), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 620, 12], fill=BRAND["light_blue"])
    d.rectangle([0, 12, 620, 24], fill=BRAND["dark_blue"])
    d.rectangle([0, 24, 620, 36], fill=BRAND["red"])
    d.text((10, 48), HANDLE, font=font, fill="white")
    im.save(logo)

fonts_opt = ":fontsdir=../assets/fonts" if any((ASSETS / "fonts").glob("*.ttf")) else ""
for c in load("clips_plan.json", []):
    src, out = SL / f"{c['id']}_m.mp4", FIN / f"{c['id']}.mp4"
    if not src.exists() or out.exists():
        continue
    ass = f"{c['id']}.ass"
    v0 = f"[0:v]ass={ass}{fonts_opt}[v0]" if (SL / ass).exists() else "[0:v]null[v0]"
    fc = f"{v0};[1:v]scale=260:-1,format=rgba,colorchannelmixer=aa=0.65[lg];[v0][lg]overlay=W-w-40:70[v]"
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{c['id']}_m.mp4", "-i", logo, "-filter_complex", fc,
         "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
         "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", out], cwd=SL)
print("الريلز النهائية في 04_final_reels")
```
