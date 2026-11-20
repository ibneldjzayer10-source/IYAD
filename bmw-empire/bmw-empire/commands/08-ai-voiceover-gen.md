# 08 — AI Voiceover (edge-tts)
**الوظيفة:** توليد تعليق صوتي مجاني عبر `edge-tts` (يحتاج إنترنت) + حفظ توقيت كل كلمة لاستخدامه في الترجمة.
**المخرجات:** `03_sliced_clips/<id>_vo.mp3` و `<id>_vo_words.json`

```python
import asyncio, os
import edge_tts
from common import *

VOICES = {"ar": os.environ.get("VOICE_AR", "ar-SA-HamedNeural"), "en": os.environ.get("VOICE_EN", "en-US-GuyNeural")}


async def gen(c):
    mp3 = SL / f"{c['id']}_vo.mp3"
    if mp3.exists():
        return
    comm = edge_tts.Communicate(c["script"], VOICES[LANG], rate="+8%", pitch="+2Hz")
    words = []
    with open(mp3, "wb") as f:
        async for ch in comm.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                words.append({"w": ch["text"], "s": ch["offset"] / 1e7, "e": (ch["offset"] + ch["duration"]) / 1e7})
    (SL / f"{c['id']}_vo_words.json").write_text(json.dumps(words, ensure_ascii=False), encoding="utf-8")
    print("✓", mp3.name, len(words), "كلمة")


async def main():
    for c in load("clips_plan.json", []):
        if c.get("script"):
            await gen(c)

asyncio.run(main())
```
