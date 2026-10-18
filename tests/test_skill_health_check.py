import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DETECTOR = REPO_ROOT / "skills" / "skill_health_check" / "scripts" / "zombie_detector.py"


class ZombieDetectorTests(unittest.TestCase):
    def test_runs_on_python37_and_ignores_generated_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skill = Path(temp_dir) / "sample-skill"
            (skill / "scripts").mkdir(parents=True)
            (skill / "output").mkdir()
            (skill / "SKILL.md").write_text(
                "---\nname: sample-skill\ndescription: Use when testing.\n---\n\n"
                "Run `scripts/run.py`.\n",
                encoding="utf-8",
            )
            (skill / "README.md").write_text("# Readme\n", encoding="utf-8")
            (skill / "README_ZH.md").write_text("# Readme ZH\n", encoding="utf-8")
            (skill / "scripts" / "run.py").write_text("print('ok')\n", encoding="utf-8")
            (skill / "output" / "old-result.md").write_text("old\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(DETECTOR), str(skill), "--print"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertNotIn("README_ZH.md", report["zombies"])
            self.assertFalse(any(path.startswith("output/") for path in report["zombies"]))


if __name__ == "__main__":
    unittest.main()
