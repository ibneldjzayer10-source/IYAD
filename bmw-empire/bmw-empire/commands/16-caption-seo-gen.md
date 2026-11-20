# 16 — Caption & SEO Generator
**الوظيفة:** وصف إنستغرام يبدأ بسؤال تفاعلي + سطرين + دعوة للتفاعل + هاشتاجات مستهدفة، ويضيف سطر المصدر عند الحاجة (CC BY). يُحفظ في `04_final_reels/<id>.meta.json`.

```python
from common import *

BASE = {"ar": ["#BMW", "#BMWM", "#بي_إم_دبليو", "#سيارات", "#MPower", "#BMWMotorsport", "#عشاق_السيارات"],
        "en": ["#BMW", "#BMWM", "#MPower", "#BMWMotorsport", "#carsofinstagram", "#cartok", "#reels"]}[LANG]
Q = {"ar": ("كم حصان يملك محرك {c}؟ 🤔", "ما رأيك في هذه اللحظة من عالم BMW M؟ 👇"),
     "en": ("How much power does the {c} really make? 🤔", "What do you think of this BMW M moment? 👇")}[LANG]
CTA = {"ar": "احفظ الريل وشاركه مع عاشق BMW 🔵⚪🔴", "en": "Save this and send it to a BMW fan 🔵⚪🔴"}[LANG]
rights = load("rights_report.json", {})

for c in load("clips_plan.json", []):
    reel = FIN / f"{c['id']}.mp4"
    if not reel.exists():
        continue
    code = c.get("engine")
    first = Q[0].format(c=code) if code else Q[1]
    body = " ".join(c["script"].split(". ")[:2]) if code else c["script"].split(". ")[0]
    tags = BASE + ([f"#{code}", f"#BMW{code}"] if code else [])
    r = rights.get(c["video_id"], {})
    credit = f"\n\n🎬 Source: {r['credit']} ({r.get('license')})" if r.get("license") else ""
    caption = f"{first}\n\n{body}\n\n{CTA}{credit}\n\n{' '.join(tags)}"
    (FIN / f"{c['id']}.meta.json").write_text(json.dumps(
        {"id": c["id"], "caption": caption, "topics": [code] if code else ["general"],
         "hook": c["script"].split(". ")[0]}, ensure_ascii=False, indent=2), encoding="utf-8")
print("تم توليد الأوصاف")
```
