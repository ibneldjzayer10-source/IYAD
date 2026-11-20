# 01 — Trend Scraper
**الوظيفة:** البحث مجاناً في يوتيوب عبر `yt-dlp` عن أكثر فيديوهات BMW انتشاراً (تاريخ، S58/B58، سباقات M) وحفظها في `trends.json` مع معلومات الرخصة.
**المخرجات:** `trends.json`

```python
import yt_dlp
from common import save

QUERIES = ["BMW S58 engine explained", "BMW B58 engine", "BMW M history documentary",
           "BMW M3 M4 race", "BMW M5 history", "BMW M-Power podcast", "BMW Nurburgring lap"]
PER_QUERY = 8

seen = {}
with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True, "ignoreerrors": True}) as ydl:
    for q in QUERIES:
        info = ydl.extract_info(f"ytsearch{PER_QUERY}:{q}", download=False) or {}
        for e in info.get("entries") or []:
            if not e or e["id"] in seen or (e.get("duration") or 0) > 3600:
                continue
            lic = e.get("license") or ""
            seen[e["id"]] = {
                "id": e["id"], "title": e.get("title"), "url": e.get("webpage_url"),
                "channel": e.get("channel") or e.get("uploader"), "views": e.get("view_count") or 0,
                "duration": e.get("duration"), "license": lic,
                "creative_commons": "creative commons" in lic.lower(), "query": q,
            }
items = sorted(seen.values(), key=lambda x: x["views"], reverse=True)
save("trends.json", items)
print(f"{len(items)} فيديو — منها {sum(i['creative_commons'] for i in items)} برخصة Creative Commons")
```
