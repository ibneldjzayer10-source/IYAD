# 07 — Script Rewriter
**الوظيفة:** يحوّل كل لقطة إلى تعليق صوتي قصير وحماسي (عربي أو إنجليزي حسب `REEL_LANG`) ويحفظه في `clips_plan.json` كحقل `script`.
**طريقتان:**
1. تلقائي مجاني (هذا السكربت): قوالب جاهزة تعتمد على البيانات من الخطوة 06.
2. جودة أعلى مع Claude Code: اطلب منه *«اقرأ clips_plan.json واكتب لكل لقطة تعليقاً صوتياً حماسياً من 25–40 كلمة بأسلوب خبير BMW، ولا تنسخ كلام المصدر، واحفظه في scripts_override.json بصيغة {clip_id: نص}»* — السكربت يفضّل هذا الملف تلقائياً.

```python
from common import *

T = {
    "ar": {
        "hook": "هل تعرف سر محرك {code}؟",
        "fact": "{name}. قوة تصل إلى {hp} حصان، وعزم {nm} نيوتن متر، وتسارع من صفر إلى مئة في حدود {accel} ثانية.",
        "generic": "لحظة من عالم بي إم دبليو M لا تُنسى. ركّز جيداً، فالتفاصيل هنا تصنع الأسطورة.",
        "cta": "تابعنا لمزيد من أسرار BMW M!",
    },
    "en": {
        "hook": "Do you know the secret behind the {code}?",
        "fact": "{name}. Up to {hp} horsepower, {nm} Nm of torque, and zero to one hundred in about {accel} seconds.",
        "generic": "An unforgettable BMW M moment. Watch closely, the details make the legend.",
        "cta": "Follow for more BMW M secrets!",
    },
}[LANG]

override = load("scripts_override.json", {})
plan = load("clips_plan.json", [])
for c in plan:
    if c["id"] in override:
        c["script"] = override[c["id"]]
        continue
    f = c.get("facts")
    if f:
        c["script"] = " ".join([T["hook"].format(code=c["engine"]), T["fact"].format(**f), T["cta"]])
    else:
        c["script"] = f"{T['generic']} {T['cta']}"
        c["needs_rewrite"] = True
save("clips_plan.json", plan)
print(len(plan), "تعليق جاهز —", sum(1 for c in plan if c.get("needs_rewrite")), "يحتاج صياغة أفضل (scripts_override.json)")
```
