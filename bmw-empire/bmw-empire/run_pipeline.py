"""تشغيل السلسلة كاملة:  python run_pipeline.py
خيارات:  --only 5 6   |  --from-step 9  |  --skip-publish  |  --dry-run  |  --lang en
كل خطوة = أول كتلة ```python داخل ملف commands/NN-*.md"""
import argparse, os, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# المسار الصحيح هو commands/ — مع بحث احتياطي في .claude/commands للتوافق مع النسخة القديمة
CMD_DIRS = [d for d in (ROOT / "commands", ROOT / ".claude" / "commands") if d.is_dir()]
# ترتيب التنفيذ الفعلي (12 قبل 08 كي لا يختل تزامن الترجمة مع التعليق الصوتي). 19 تُشغَّل عند الطلب.
ORDER = [1, 2, 3, 4, 5, 6, 7, 9, 10, 12, 8, 11, 13, 14, 15, 16, 17, 18, 20]
NON_FATAL = {20}


def code_of(n):
    searched = []
    for d in CMD_DIRS:
        searched.append(str(d))
        matches = sorted(d.glob(f"{n:02d}-*.md"))
        if matches:
            f = matches[0]
            m = re.search(r"```python\n(.*?)```", f.read_text(encoding="utf-8"), re.S)
            if not m:
                sys.exit(f"!! لا توجد كتلة ```python داخل {f.name}")
            return f.name, m.group(1)
    where = ", ".join(searched) if searched else "لا يوجد مجلد commands/ ولا .claude/commands/"
    sys.exit(f"!! لم يُعثر على ملف أمر للخطوة {n:02d} — بحثت في: {where}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", type=int, nargs="*")
    ap.add_argument("--from-step", type=int, default=0)
    ap.add_argument("--skip-publish", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--lang")
    a = ap.parse_args()
    env = dict(os.environ, PYTHONPATH=str(ROOT), PYTHONIOENCODING="utf-8")
    if a.dry_run: env["DRY_RUN"] = "1"
    if a.lang: env["REEL_LANG"] = a.lang
    steps = a.only or [n for n in ORDER if n >= a.from_step]
    if a.skip_publish: steps = [n for n in steps if n != 18]
    for n in steps:
        name, code = code_of(n)
        print(f"\n=== [{n:02d}] {name} ===")
        r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=env)
        if r.returncode != 0:
            print(f"!! فشلت الخطوة {n:02d}")
            if n not in NON_FATAL: sys.exit(r.returncode)
    print("\n✅ انتهت السلسلة")


if __name__ == "__main__":
    main()
