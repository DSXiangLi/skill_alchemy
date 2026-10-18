import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / "meta_skill" / "skills" / "skill-alchemy"
SCRIPTS_DIR = SKILL_DIR / "scripts"
DISTILL = SCRIPTS_DIR / "distill.py"


def load_module(name, path):
    sys.path.insert(0, str(path.parent))
    try:
        spec = importlib.util.spec_from_file_location(name, str(path))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.pop(0)


distill = load_module("skill_alchemy_distill", DISTILL)
extract = load_module("skill_alchemy_extract", SCRIPTS_DIR / "extract.py")
validate_run = load_module("skill_alchemy_validate_run", SCRIPTS_DIR / "validate_run.py")


class TimestampTests(unittest.TestCase):
    def test_created_at_takes_precedence(self):
        session = {
            "created_at": "2026-09-05T12:30:00+00:00",
            "source_file": "/missing/rollout-2020-01-01T00-00-00-old.jsonl",
        }
        expected = distill.datetime.fromisoformat(session["created_at"]).timestamp()
        self.assertEqual(distill.get_session_timestamp(session), expected)

    def test_codex_filename_timestamp_is_parsed(self):
        session = {
            "created_at": "",
            "source_file": "/missing/rollout-2026-08-22T19-06-22-abc.jsonl",
        }
        self.assertGreater(distill.get_session_timestamp(session), 0)

    def test_extractor_captures_event_timestamp(self):
        timestamp = "2026-09-05T08:00:00Z"
        self.assertEqual(
            extract.infer_created_at("/missing", [{"timestamp": timestamp}]),
            timestamp,
        )


class DistillCliTests(unittest.TestCase):
    def make_input(self, root):
        input_path = root / "sessions.jsonl"
        sessions = [
            {
                "source_tool": "codex",
                "source_file": "/missing/rollout-2026-09-01T10-00-00-a.jsonl",
                "session_id": "old",
                "created_at": "2026-09-01T10:00:00+00:00",
                "workspace": "/project/a",
                "turns": [{"user": "old question", "assistant": "old answer"}],
            },
            {
                "source_tool": "claude_code",
                "source_file": "/missing/new.jsonl",
                "session_id": "new",
                "created_at": "2026-09-03T10:00:00+00:00",
                "workspace": "/project/a",
                "turns": [{"user": "new question", "assistant": "new answer"}],
            },
            {
                "source_tool": "hermes_agent",
                "source_file": "/missing/middle.json",
                "session_id": "middle",
                "created_at": "2026-09-02T10:00:00+00:00",
                "workspace": "/project/a",
                "turns": [{"user": "middle question", "assistant": "middle answer"}],
            },
        ]
        with input_path.open("w", encoding="utf-8") as handle:
            for session in sessions:
                handle.write(json.dumps(session) + "\n")
        return input_path

    def run_distill(self, input_path, output_path, *extra):
        return subprocess.run(
            [sys.executable, str(DISTILL), str(input_path), "-o", str(output_path)]
            + list(extra),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def test_default_run_preserves_boundaries_and_sorts_newest_first(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            result = self.run_distill(self.make_input(root), root / "run")
            self.assertEqual(result.returncode, 0, result.stderr)

            anchor = (root / "run" / "anchor_recent.md").read_text(encoding="utf-8")
            self.assertEqual(anchor.count("<!-- BEGIN_SESSION "), 3)
            self.assertEqual(anchor.count("<!-- END_SESSION "), 3)
            self.assertLess(anchor.index("# Session new"), anchor.index("# Session middle"))
            self.assertLess(anchor.index("# Session middle"), anchor.index("# Session old"))

            instruction = (root / "run" / "ANALYSIS_INSTRUCTION.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("## Phase 6: First-Layer Artifacts", instruction)
            self.assertIn("## Phase 7: Skill Synthesis", instruction)

    def test_recent_and_max_sessions_must_be_positive(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_path = self.make_input(root)
            for option, value in (("--recent", "0"), ("--recent", "-1"), ("--max-sessions", "0")):
                result = self.run_distill(input_path, root / (option + value), option, value)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("must be at least 1", result.stderr)


class FirstLayerValidationTests(unittest.TestCase):
    def test_first_layer_accepts_evidence_and_explicit_empty_results(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            contents = {
                "action-guides": "Session ID: s1, Turn 1\n",
                "error-patterns": "session_id: s1, turn_index: 1\n",
                "repeated-requirements": "None found\n",
                "conflicting-requirements": "未发现\n",
                "related-findings": "Structured evidence: session s1 turn 1\n",
            }
            for directory, content in contents.items():
                path = root / directory
                path.mkdir()
                (path / "result.md").write_text(content, encoding="utf-8")

            result = validate_run.validate_first_layer(str(root))
            self.assertEqual(result["artifact_files"], 5)

    def test_first_layer_rejects_missing_evidence(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for directory in validate_run.FIRST_LAYER_DIRS:
                path = root / directory
                path.mkdir()
                (path / "result.md").write_text("summary only\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                validate_run.validate_first_layer(str(root))


if __name__ == "__main__":
    unittest.main()
