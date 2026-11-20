# 06 — BMW Fact Enricher
**الوظيفة:** يكتشف رمز المحرك في نص كل لقطة (S58, B58, …) ويضيف الأحصنة والعزم والتسارع إلى `clips_plan.json`.
**تنبيه:** الأرقام مرجعية تقريبية وتختلف بين الموديلات والسنوات. راجعها قبل النشر وعدّل القاموس حسب الحاجة.

```python
import re
from common import *

ENGINES = {
    "S58": {"name": "BMW S58 (3.0L twin-turbo I6)", "hp": "453–543", "nm": "550–650", "accel": "3.4–3.9"},
    "B58": {"name": "BMW B58 (3.0L turbo I6)", "hp": "335–382", "nm": "450–500", "accel": "4.1–4.4"},
    "S55": {"name": "BMW S55 (3.0L twin-turbo I6)", "hp": "425–493", "nm": "550–600", "accel": "3.9–4.3"},
    "S63": {"name": "BMW S63 (4.4L twin-turbo V8)", "hp": "560–627", "nm": "680–750", "accel": "3.3–4.2"},
    "S65": {"name": "BMW S65 (4.0L V8)", "hp": "414", "nm": "400", "accel": "4.8"},
    "S85": {"name": "BMW S85 (5.0L V10)", "hp": "500", "nm": "520", "accel": "4.7"},
    "S54": {"name": "BMW S54 (3.2L I6)", "hp": "338", "nm": "365", "accel": "5.0"},
    "N54": {"name": "BMW N54 (3.0L twin-turbo I6)", "hp": "302–335", "nm": "400–450", "accel": "5.1"},
}
plan = load("clips_plan.json", [])
for c in plan:
    m = re.search(r"\b(" + "|".join(ENGINES) + r")\b", c["text"], re.I)
    if m:
        code = m.group(1).upper()
        c["engine"] = code
        c["facts"] = {**ENGINES[code], "verified": False}
    else:
        c["engine"], c["facts"] = None, None
save("clips_plan.json", plan)
print(sum(1 for c in plan if c["facts"]), "لقطة أُضيفت لها بيانات تقنية")
```
