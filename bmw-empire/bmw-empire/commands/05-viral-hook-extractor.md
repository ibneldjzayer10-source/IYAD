# 05 — Viral Hook Extractor
**الوظيفة:** يحلل `02_transcripts` (للمقاطع المعتمدة فقط) ويختار أفضل 15 لقطة (20–45 ثانية) بنظام نقاط: كلمات BMW المفتاحية، الأرقام، الحماس، كثافة الكلام.
**المخرجات:** `clips_plan.json`
**ملاحظة:** التقييم هنا بقواعد محلية مجانية. لتقييم أذكى شغّل هذا الملف داخل Claude Code واطلب منه تعديل `clips_plan.json`.

```python
import re
from common import *

KW = ["horsepower", " hp", "torque", "nm", "m3", "m4", "m5", "m2", "s58", "b58", "s55", "s63", "v8", "v10",
      "straight-six", "inline-six", "turbo", "record", "fastest", "insane", "nurburgring", "nürburgring",
      "lap", "legend", "history", "race", "0-60", "0-100", "csl", "motorsport", "جيل", "محرك", "حصان", "سباق"]
MIN_D, MAX_D, TOP = 20, 45, 15


def score(text, dur):
    t = text.lower()
    return (sum(2 for k in KW if k in t) + len(re.findall(r"\d+", t)) + t.count("!")
            + min(len(t.split()) / dur, 4))


cands = []
ok = cleared_ids()
for f in sorted(TR.glob("*.json")):
    d = json.loads(f.read_text(encoding="utf-8"))
    if d["id"] not in ok:
        continue
    segs = d["segments"]
    for i in range(len(segs)):
        end_i, texts = None, []
        for j in range(i, len(segs)):
            dur = segs[j]["end"] - segs[i]["start"]
            if dur > MAX_D:
                break
            texts.append(segs[j]["text"])
            if dur >= MIN_D:
                end_i = j
        if end_i is None:
            continue
        text = " ".join(s["text"] for s in segs[i:end_i + 1])
        st, en = segs[i]["start"], segs[end_i]["end"]
        cands.append({"video_id": d["id"], "start": round(st, 2), "end": round(en, 2),
                      "text": text, "score": round(score(text, en - st), 2)})

cands.sort(key=lambda c: c["score"], reverse=True)
plan = []
for c in cands:
    if any(p["video_id"] == c["video_id"] and c["start"] < p["end"] and c["end"] > p["start"] for p in plan):
        continue
    c["id"] = f"{c['video_id']}_{int(c['start'])}"
    plan.append(c)
    if len(plan) == TOP:
        break
save("clips_plan.json", plan)
print(f"{len(plan)} لقطة في clips_plan.json")
```
