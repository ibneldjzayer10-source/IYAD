# 19 — Comment Reply Helper
**الوظيفة:** يولّد ردوداً بأسلوب خبير BMW على التعليقات. ضع التعليقات في `comments.json` بصيغة `[{"id":"1","user":"x","text":"..."}]` فيُنتج `replies.json` للمراجعة قبل النشر اليدوي (لا ينشر الردود تلقائياً).
**للجودة الأعلى:** شغّله داخل Claude Code واطلب منه كتابة الردود بنفسه لكل تعليق بنبرة الحساب.

```python
import re
from common import *

RULES = [
    (r"hp|horsepower|حصان|قوة", {"ar": "القوة تختلف حسب الموديل والسنة، والأرقام الدقيقة في الفيديو 💪 أي موديل يهمك؟",
                                  "en": "Power varies by model and year 💪 Which model are you after?"}),
    (r"price|سعر|كم يكلف|cost", {"ar": "السعر يتفاوت حسب السوق والمواصفات، تفقد الوكيل المحلي 🔎",
                                  "en": "Price depends on market and spec, check your local dealer 🔎"}),
    (r"m3|m4|m5|m2", {"ar": "سلسلة M دائماً خيار قوي! أيهما تفضّل: سيدان أم كوبيه؟ 🔥",
                       "en": "The M cars never disappoint! Sedan or coupe? 🔥"}),
    (r"s58|b58|engine|محرك", {"ar": "من أعظم محركات الست أسطوانات الحديثة، أي محرك تريدنا نشرحه بعده؟ ⚙️",
                               "en": "One of the best modern sixes. Which engine should we cover next? ⚙️"}),
    (r"❤|🔥|love|رائع|روعة|حلو", {"ar": "شكراً لدعمك! 🔵⚪🔴", "en": "Thanks for the love! 🔵⚪🔴"}),
]
DEFAULT = {"ar": "شكراً لتعليقك! ما الموديل المفضل لديك؟ 🏁", "en": "Thanks! What's your favorite BMW? 🏁"}
out = []
for cm in load("comments.json", []):
    reply = next((r[LANG] for p, r in RULES if re.search(p, cm["text"], re.I)), DEFAULT[LANG])
    out.append({**cm, "reply": reply})
save("replies.json", out)
print(len(out), "رد في replies.json — راجعها قبل النشر")
```
