"""اختبارات الإعداد — بلا مكتبات خارجية:
    python3 -m unittest discover -s tests -v
"""
import ast
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bmw-empire" / "bmw-empire"))
COMMANDS = ROOT / "bmw-empire" / "bmw-empire" / "commands"


class TopicsSchemaTests(unittest.TestCase):
    """topics.txt العمود الفقري للمحتوى: أي سطر ناقص يكسر التشغيل المجدول."""

    def test_every_pipe_line_has_three_non_empty_parts(self):
        lines = [
            ln
            for ln in (ROOT / "topics.txt").read_text(encoding="utf-8").splitlines()
            if "|" in ln
        ]
        self.assertGreater(len(lines), 0, "topics.txt فارغ أو بلا فواصل |")
        for i, ln in enumerate(lines, 1):
            parts = [p.strip() for p in ln.split("|")]
            self.assertEqual(len(parts), 3, f"سطر {i}: {len(parts)} أقسام بدل 3")
            self.assertTrue(all(parts), f"سطر {i}: يوجد قسم فارغ")


class PublishScriptTests(unittest.TestCase):
    """سكربت النشر: صحيحاً نحوياً ومحفوظاً بضمانات المراجعة."""

    def setUp(self):
        self.src = (ROOT / "scripts" / "publish_reel.py").read_text(encoding="utf-8")

    def test_script_parses(self):
        ast.parse(self.src)

    def test_safety_guards_present(self):
        self.assertIn("retries=3", self.src)        # gdown 6.x حذفت remaining_ok
        self.assertNotIn("remaining_ok=True", self.src)
        self.assertIn("already_published", self.src)  # منع نشر الوصف المكرر
        self.assertIn("status_code >= 300", self.src)  # فحص حقيقي لردود API
        self.assertIn("os.chdir(ROOT)", self.src)

    def test_workflow_calls_script(self):
        wf_path = ROOT / ".github" / "workflows" / "main.yml"
        wf = wf_path.read_text(encoding="utf-8")
        self.assertIn("scripts/publish_reel.py", wf)
        self.assertIn("timeout-minutes", wf)
        self.assertIn("concurrency", wf)
        self.assertIn("dry_run", wf)
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML غير مثبت — فحص YAML يتخطى محلياً")
        yaml.safe_load(wf)


class PipelineTests(unittest.TestCase):
    """run_pipeline.py وملفات الأوامر الـ20."""

    def test_code_of_reads_every_step(self):
        import run_pipeline  # آمن: لا تأثيرات جانبية عند الاستيراد

        self.assertTrue(run_pipeline.CMD_DIRS, "لا يوجد مجلد commands/ (أو .claude/commands/)")
        for n in run_pipeline.ORDER:
            name, code = run_pipeline.code_of(n)
            ast.parse(code, filename=name)

    def test_missing_step_gives_clear_error(self):
        import run_pipeline

        with self.assertRaises(SystemExit):
            run_pipeline.code_of(99)

    def test_commands_are_twenty_files_with_balanced_fences(self):
        files = sorted(COMMANDS.glob("*.md"))
        self.assertEqual(len(files), 20, f"عدد ملفات الأوامر {len(files)} بدل 20")
        for f in files:
            text = f.read_text(encoding="utf-8")
            self.assertEqual(
                len(re.findall(r"^```", text, re.M)) % 2, 0,
                f"{f.name}: فواصل ``` فردية (سياج ناقص أو زائد)",
            )
            self.assertEqual(
                len(re.findall(r"```python", text)), 1,
                f"{f.name}: يجب أن يحوي كتلة ```python واحدة بالضبط",
            )


if __name__ == "__main__":
    unittest.main()
