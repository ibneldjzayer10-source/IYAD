# 18 — Safe API Publisher (Late API → Instagram Reel)
**الوظيفة:** يرفع كل ريل جاهز في `04_final_reels` وينشره على إنستغرام عبر Late API بمفتاح `LATE_API_KEY` من `.env`، ثم ينقله مع ملفاته إلى `05_published` ويسجّل `published_log.json`.
**أمان:** `MAX_POSTS_PER_RUN` (افتراضي 3) و `DRY_RUN=1` للتجربة بلا نشر. المفتاح لا يُطبع أبداً.
**تنبيه:** نقاط الـ API (المسارات وأسماء الحقول) كُتبت من معرفتي بتوثيق Late دون إمكانية اختبارها هنا، فتأكد منها في getlate.dev/docs وعدّل الثوابت أعلى السكربت عند الحاجة. وقبل أول نشر فعلي شغّل `--dry-run`، وتأكد أن حساب إنستغرام مربوط في لوحة Late.

```python
import os, shutil, time
import requests
from common import *

BASE = os.environ.get("LATE_BASE_URL", "https://getlate.dev/api/v1")
KEY = os.environ.get("LATE_API_KEY")
DRY = os.environ.get("DRY_RUN", "0") == "1"
MAX_POSTS = int(os.environ.get("MAX_POSTS_PER_RUN", "3"))
H = {"Authorization": f"Bearer {KEY}"}

if not KEY and not DRY:
    raise SystemExit("LATE_API_KEY غير موجود في .env")


def instagram_account_id():
    r = requests.get(f"{BASE}/accounts", headers=H, timeout=30)
    r.raise_for_status()
    data = r.json()
    for a in (data.get("accounts", data) if isinstance(data, dict) else data):
        if a.get("platform") == "instagram":
            return a.get("_id") or a.get("id")
    raise SystemExit("لا يوجد حساب إنستغرام مربوط في Late")


def upload(path):
    with open(path, "rb") as f:
        r = requests.post(f"{BASE}/media", headers=H, files={"files": (path.name, f, "video/mp4")}, timeout=900)
    r.raise_for_status()
    d = r.json()
    files = d.get("files") or d.get("media") or [d]
    return files[0]["url"]


ready = sorted(FIN.glob("*.mp4"))[:MAX_POSTS]
if not ready:
    print("لا توجد ريلز جاهزة")
acc = None if DRY or not ready else instagram_account_id()
log = load("published_log.json", [])
for mp4 in ready:
    meta_f = FIN / f"{mp4.stem}.meta.json"
    meta = json.loads(meta_f.read_text(encoding="utf-8")) if meta_f.exists() else {"caption": "", "topics": []}
    if DRY:
        print("[DRY] كان سينشر:", mp4.name, "\n", meta["caption"][:120])
        continue
    body = {"content": meta["caption"], "mediaItems": [{"type": "video", "url": upload(mp4)}],
            "platforms": [{"platform": "instagram", "accountId": acc,
                           "platformSpecificData": {"contentType": "reels"}}],
            "publishNow": True}
    r = requests.post(f"{BASE}/posts", headers=H, json=body, timeout=120)
    if r.status_code >= 300:
        print("✗ فشل النشر", mp4.name, r.status_code, r.text[:300])
        continue
    d = r.json()
    post = d.get("post", d)
    log.append({"id": mp4.stem, "post_id": post.get("_id") or post.get("id"), "topics": meta.get("topics", []),
                "hook": meta.get("hook"), "published_at": time.strftime("%Y-%m-%d %H:%M:%S")})
    for f in FIN.glob(f"{mp4.stem}*"):
        shutil.move(str(f), PUB / f.name)
    save("published_log.json", log)
    print("✅ نُشر:", mp4.name)
```
