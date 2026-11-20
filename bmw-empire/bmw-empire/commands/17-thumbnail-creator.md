# 17 — Thumbnail Creator
**الوظيفة:** يختار أوضح إطار (حدة + إضاءة) من الريل ويكتب عليه عنواناً عريضاً بشريط ألوان BMW M، ويحفظه `04_final_reels/<id>_cover.jpg`. للعربية ضع خطاً عربياً في `assets/fonts/`.

```python
import textwrap
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
from common import *

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    shape = lambda t: get_display(arabic_reshaper.reshape(t)) if LANG == "ar" else t
except ImportError:
    shape = lambda t: t

fonts = sorted((ASSETS / "fonts").glob("*.ttf"))
try:
    font = ImageFont.truetype(str(fonts[0]) if fonts else "DejaVuSans-Bold.ttf", 96)
except OSError:
    font = ImageFont.load_default()

for c in load("clips_plan.json", []):
    reel, out = FIN / f"{c['id']}.mp4", FIN / f"{c['id']}_cover.jpg"
    if not reel.exists() or out.exists():
        continue
    cap = cv2.VideoCapture(str(reel))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    best, best_s = None, -1
    for i in np.linspace(n * 0.1, n * 0.9, 24).astype(int):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(i))
        ok, fr = cap.read()
        if ok:
            g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
            s = cv2.Laplacian(g, cv2.CV_64F).var() * (0.5 + g.mean() / 255)
            if s > best_s:
                best, best_s = fr, s
    cap.release()
    if best is None:
        continue
    im = Image.fromarray(cv2.cvtColor(best, cv2.COLOR_BGR2RGB)).convert("RGBA")
    W, H = im.size
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    d.rectangle([0, int(H * 0.62), W, H], fill=(0, 51, 102, 215))
    d.rectangle([0, int(H * 0.62), W, int(H * 0.62) + 14], fill=BRAND["red"])
    title = (c.get("engine") + "؟ " if c.get("engine") and LANG == "ar" else "") + c["script"].split(". ")[0]
    lines = textwrap.wrap(title, 16 if LANG == "ar" else 18)[:3]
    y = int(H * 0.66)
    for ln in lines:
        w = d.textlength(shape(ln), font=font)
        d.text(((W - w) / 2, y), shape(ln), font=font, fill=BRAND["light_blue"] if y == int(H * 0.66) else "white")
        y += 115
    Image.alpha_composite(im, ov).convert("RGB").save(out, quality=92)
    print("✓", out.name)
```
