# 03 — Transcribe Audio
**الوظيفة:** تفريغ الصوت بـ `faster-whisper` (مجاني ومحلي) مع توقيت دقيق لكل جملة وكلمة.
**المخرجات:** `02_transcripts/<id>.json` — اضبط `WHISPER_MODEL` (tiny/base/small/medium).

```python
import os
from faster_whisper import WhisperModel
from common import *

model = WhisperModel(os.environ.get("WHISPER_MODEL", "small"), device="auto", compute_type="int8")
for p in sorted(RAW.iterdir()):
    if p.suffix.lower() not in (".mp4", ".mkv", ".webm", ".mov"):
        continue
    out = TR / f"{p.stem}.json"
    if out.exists():
        continue
    segs, info = model.transcribe(str(p), word_timestamps=True, vad_filter=True)
    data = {"id": p.stem, "language": info.language, "segments": [
        {"start": s.start, "end": s.end, "text": s.text.strip(),
         "words": [{"w": w.word.strip(), "s": w.start, "e": w.end} for w in (s.words or [])]}
        for s in segs]}
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("✓", out.name, info.language)
```
