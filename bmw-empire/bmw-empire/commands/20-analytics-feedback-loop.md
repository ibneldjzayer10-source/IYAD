# 20 — Analytics Feedback Loop
**الوظيفة:** يقرأ `published_log.json` + أرقام التفاعل (من `metrics.json` يدوياً بصيغة `{post_id:{views,likes,comments,saves}}`، أو يحاول جلبها من Late API إن توفر)، يحسب التفاعل لكل موضوع، ثم يحدّث قسم `AUTO:TOPICS` في `CLAUDE.md`.
**تنبيه:** نقطة جلب التحليلات في Late لم أتحقق منها؛ إن فشلت يستخدم `metrics.json` ولا يتوقف.

```python
import os, re
import requests
from collections import defaultdict
from common import *

log, metrics = load("published_log.json", []), load("metrics.json", {})
BASE, KEY = os.environ.get("LATE_BASE_URL", "https://zernio.com/api/v1"), os.environ.get("LATE_API_KEY")
if KEY:
    for p in log:
        if p["post_id"] and p["post_id"] not in metrics:
            try:
                r = requests.get(f"{BASE}/analytics", params={"postId": p["post_id"]},
                                 headers={"Authorization": f"Bearer {KEY}"}, timeout=30)
                if r.ok:
                    a = r.json().get("analytics", r.json())
                    metrics[p["post_id"]] = {k: a.get(k, 0) for k in ("views", "likes", "comments", "saves")}
            except requests.RequestException:
                pass
    save("metrics.json", metrics)

agg = defaultdict(lambda: [0.0, 0])
for p in log:
    m = metrics.get(p["post_id"])
    if not m:
        continue
    s = (m.get("likes", 0) + 2 * m.get("comments", 0) + 3 * m.get("saves", 0)) / max(m.get("views", 0), 1)
    for t in p.get("topics", ["general"]):
        agg[t][0] += s
        agg[t][1] += 1
ranked = sorted(((t, v[0] / v[1], v[1]) for t, v in agg.items()), key=lambda x: x[1], reverse=True)
lines = ["## المواضيع الأعلى تفاعلاً (تحديث تلقائي)"] + [
    f"{i}. **{t}** — معدل التفاعل {s:.3f} ({n} منشور)" for i, (t, s, n) in enumerate(ranked, 1)]
lines.append("→ ركّز المحتوى القادم على أعلى 2–3 مواضيع، وكرّر الصيغ التي نجحت.")
block = "<!-- AUTO:TOPICS -->\n" + ("\n".join(lines) if ranked else "(لا بيانات تفاعل بعد)") + "\n<!-- /AUTO:TOPICS -->"
md = ROOT / "CLAUDE.md"
txt = md.read_text(encoding="utf-8")
md.write_text(re.sub(r"<!-- AUTO:TOPICS -->.*?<!-- /AUTO:TOPICS -->", lambda _: block, txt, flags=re.S), encoding="utf-8")
print("تم تحديث CLAUDE.md —", len(ranked), "موضوع")
```
