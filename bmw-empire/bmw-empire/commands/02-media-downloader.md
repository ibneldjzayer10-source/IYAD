# 02 — Media Downloader
**الوظيفة:** تحميل فيديوهات `trends.json` بأعلى جودة إلى `01_raw_media`.
**قيد مهم:** يُحمَّل فقط ما رخصته Creative Commons أو ما أضفتَه إلى `approved_urls.txt` (مصادر تملكها أو لديك إذن بها). `MAX_DOWNLOADS` يحدد العدد.

```python
import yt_dlp
from common import *

MAX_DOWNLOADS = 10
approved = approved_ids()
items = load("trends.json", [])
todo = [i for i in items if i["creative_commons"] or i["id"] in approved][:MAX_DOWNLOADS]
# مصادر معتمدة يدوياً غير موجودة في trends.json
known = {i["id"] for i in items}
extra = [{"id": a, "url": f"https://www.youtube.com/watch?v={a}"} for a in approved if a not in known]
todo += extra
if not todo:
    print("لا توجد مصادر مسموح بتحميلها. أضف روابط إلى approved_urls.txt أو شغّل 01 للبحث عن Creative Commons.")

opts = {"format": "bestvideo*+bestaudio/best", "merge_output_format": "mp4",
        "outtmpl": str(RAW / "%(id)s.%(ext)s"), "ignoreerrors": True, "noprogress": True}
with yt_dlp.YoutubeDL(opts) as ydl:
    for it in todo:
        if find_video(it["id"]):
            continue
        ydl.download([it["url"]])
print("تم. الملفات في 01_raw_media")
```
