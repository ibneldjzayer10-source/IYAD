# 10 — Smart Crop 9:16
**الوظيفة:** تحويل 16:9 إلى 9:16 (1080×1920) مع تتبع: وجه المتحدث إن وُجد (OpenCV Haar)، وإلا مركز الحركة (يلتقط السيارة المتحركة غالباً). الحركة تُنعَّم وتُطبَّق عبر `sendcmd` في FFmpeg.
**المخرجات:** `03_sliced_clips/<id>_v.mp4`

```python
import cv2, numpy as np
from common import *

try:
    FACE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    if FACE.empty():
        FACE = None
except Exception:
    FACE = None  # بدون كاشف وجوه: يعتمد التتبع على مركز الحركة فقط


def track(path):
    cap = cv2.VideoCapture(str(path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    w, h = int(cap.get(3)), int(cap.get(4))
    step, xs, prev, i = max(1, int(fps * 0.5)), [], None, 0
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        if i % step == 0:
            small = cv2.resize(cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY), (w // 4, h // 4))
            faces = FACE.detectMultiScale(small, 1.2, 5, minSize=(20, 20)) if FACE is not None else []
            if len(faces):
                x, y, fw, fh = max(faces, key=lambda f: f[2] * f[3])
                cx = (x + fw / 2) * 4
            elif prev is not None:
                col = cv2.absdiff(small, prev).sum(axis=0).astype(float)
                cx = (np.arange(len(col)) * col).sum() / col.sum() * 4 if col.sum() > 0 else w / 2
            else:
                cx = w / 2
            prev = small
            xs.append(cx)
        i += 1
    cap.release()
    return xs, step / fps, w, h


for c in load("clips_plan.json", []):
    src, out = SL / f"{c['id']}.mp4", SL / f"{c['id']}_v.mp4"
    if not src.exists() or out.exists():
        continue
    xs, dt, w, h = track(src)
    if w <= h:  # عمودي أصلاً
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-vf",
             "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920", "-c:a", "copy", out])
        continue
    cw = int(h * 9 / 16) // 2 * 2
    k = 5
    pad = np.pad(xs, (k // 2, k // 2), mode="edge")
    sm = np.convolve(pad, np.ones(k) / k, mode="valid")
    cmds, last = [], None
    for n, cx in enumerate(sm):
        x = int(min(max(cx - cw / 2, 0), w - cw))
        if last is None or abs(x - last) > 40:
            cmds.append(f"{n * dt:.2f} crop@c x {x};")
            last = x
    (SL / f"{c['id']}.cmd").write_text("\n".join(cmds), encoding="utf-8")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{c['id']}.mp4", "-vf",
         f"sendcmd=f={c['id']}.cmd,crop@c=w={cw}:h={h}:x=0:y=0,scale=1080:1920,setsar=1",
         "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-c:a", "copy", f"{c['id']}_v.mp4"], cwd=SL)
print("تم التحويل العمودي")
```
