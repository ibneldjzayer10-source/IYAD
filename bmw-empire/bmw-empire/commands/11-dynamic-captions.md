# 11 — Dynamic Captions
**الوظيفة:** ترجمة كلمة بكلمة في منتصف الشاشة بألوان BMW M (أزرق فاتح/أبيض/أحمر مع إطار أزرق داكن) وحركة تكبير سريعة. تُنتج ملف ASS يُدمج في الخطوة 15.
**الخط:** ضع خطاً عربياً (مثل Cairo) في `assets/fonts/` واضبط `CAPTION_FONT`.

```python
import os
from common import *

FONT = os.environ.get("CAPTION_FONT", "Arial")
LB, DB, RD, WH = "&H00E9A000", "&H00663300", "&H001A00E2", "&H00FFFFFF"  # BGR لـ #00A0E9 #003366 #E2001A
HEAD = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Main,{FONT},120,{WH},&H000000FF,{DB},&H00000000,-1,0,0,0,100,100,0,0,1,8,2,5,60,60,0,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""


def ts(t):
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


for c in load("clips_plan.json", []):
    wf, mp3 = SL / f"{c['id']}_vo_words.json", SL / f"{c['id']}_vo.mp3"
    if not mp3.exists():
        continue
    words = json.loads(wf.read_text(encoding="utf-8")) if wf.exists() else []
    if not words:  # تقدير بالتساوي إن لم يتوفر توقيت الكلمات
        toks, total = c["script"].split(), duration(mp3)
        words = [{"w": t, "s": total * i / len(toks), "e": total * (i + 1) / len(toks)} for i, t in enumerate(toks)]
    lines = []
    for i, w in enumerate(words):
        end = words[i + 1]["s"] if i + 1 < len(words) else w["e"]
        txt = w["w"].upper() if LANG == "en" else w["w"]
        col = [LB, WH, RD][i % 3]
        lines.append(f"Dialogue: 0,{ts(w['s'])},{ts(end)},Main,,0,0,0,,"
                     "{\\c" + col + "\\fscx120\\fscy120\\t(0,120,\\fscx100\\fscy100)}" + txt)
    (SL / f"{c['id']}.ass").write_text(HEAD + "\n".join(lines), encoding="utf-8")
print("تم توليد الترجمة")
```
