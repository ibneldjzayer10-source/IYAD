```python
import re, subprocess
from common import *

KW = ["horsepower", " hp", "torque", "nm", "m3", "m4", "m5", "m2", "s58", "b58", "s55", "s63", "v8", "v10",
      "straight-six", "inline-six", "turbo", "record", "fastest", "insane", "nurburgring", "nürburgring",
      "lap", "legend", "history", "race", "0-60", "0-100", "csl", "motorsport", "جيل", "محرك", "حصان", "سباق", "بي ام"]
MIN_D, MAX_D, TOP = 15, 45, 5


def score(text, dur):
    t = text.lower()
    return (sum(2 for k in KW if k in t) + len(re.findall(r"\d+", t)) + t.count("!")
            + min(len(t.split()) / max(dur, 1), 4))


cands = []
for f in sorted(TR.glob("*.json")):
    d = json.loads(f.read_text(encoding="utf-8"))
    segs = d.get("segments", [])
    for i in range(len(segs)):
        end_i = None
        for j in range(i, len(segs)):
            dur = segs[j]["end"] - segs[i]["start"]
            if dur > MAX_D:
                break
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

if not plan:
    for vid in sorted(RAW.glob("*.mp4")):
        for idx, start in enumerate([10, 45, 80]):
            plan.append({
                "id": f"{vid.stem}_{start}",
                "video_id": vid.stem,
                "start": start,
                "end": start + 25,
                "text": "أسطورة هندسة محركات BMW M Power وأداؤها الخارق على الحلبات!",
                "score": 10.0
            })
        break

save("clips_plan.json", plan)
print(f"{len(plan)} لقطة في clips_plan.json")
```
