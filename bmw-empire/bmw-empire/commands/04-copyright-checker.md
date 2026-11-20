# 04 — Rights Checker (فاحص الحقوق)
**الوظيفة:** يفحص كل ملف في `01_raw_media` ويصدر `rights_report.json`. لا تمر إلى بقية الخطوات إلا المقاطع «المعتمدة»: رخصة Creative Commons، أو مصدر أضفتَه في `approved_urls.txt`.
**ملاحظة:** لم أبنِ فلاتر «تغيير السرعة 1.03x/تعديل التردد» لأنها تُستخدم للتحايل على أنظمة كشف حقوق النشر ولا تجعل المحتوى استخداماً عادلاً. البديل الصحيح: مصادر مرخّصة + تعليق صوتي أصلي + ذكر المصدر.

```python
from common import *

trends = {t["id"]: t for t in load("trends.json", [])}
approved = approved_ids()
report = {}
for p in sorted(RAW.iterdir()):
    if p.suffix.lower() not in (".mp4", ".mkv", ".webm", ".mov"):
        continue
    t = trends.get(p.stem, {})
    cc = bool(t.get("creative_commons"))
    ok = cc or p.stem in approved
    report[p.stem] = {
        "cleared": ok,
        "reason": "Creative Commons" if cc else ("approved_urls.txt" if ok else "no license — not cleared"),
        "license": t.get("license"),
        "credit": f"{t.get('title', p.stem)} — {t.get('channel', '?')} ({t.get('url', '')})",
    }
save("rights_report.json", report)
for k, v in report.items():
    print(("✅" if v["cleared"] else "⛔"), k, v["reason"])
```
