#!/usr/bin/env python3
"""Validate Skill Alchemy organizer outputs."""

import argparse
import os
import re
import sys


REQUIRED_FILES = (
    "anchor_recent.md",
    "session_index.md",
    "ANALYSIS_INSTRUCTION.md",
)

FIRST_LAYER_DIRS = (
    "action-guides",
    "error-patterns",
    "repeated-requirements",
    "conflicting-requirements",
    "related-findings",
)

EVIDENCE_PATTERN = re.compile(
    r"session(?:_id)?|turn(?:_index)?|structured evidence|结构化证据",
    re.IGNORECASE,
)
NO_EVIDENCE_PATTERN = re.compile(r"none found|no evidence|未发现|无证据", re.IGNORECASE)


def positive_int(value):
    try:
        parsed = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("must be an integer")
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed


def validate_run(run_dir, expected_recent=None, expected_index=None):
    """Validate required files, session boundaries, index coverage, and phase contract."""
    errors = []
    paths = {name: os.path.join(run_dir, name) for name in REQUIRED_FILES}
    for name, path in paths.items():
        if not os.path.isfile(path):
            errors.append("missing required file: {}".format(name))

    if errors:
        raise ValueError("; ".join(errors))

    with open(paths["anchor_recent.md"], encoding="utf-8") as f:
        anchor_text = f.read()
    with open(paths["session_index.md"], encoding="utf-8") as f:
        index_text = f.read()
    with open(paths["ANALYSIS_INSTRUCTION.md"], encoding="utf-8") as f:
        instruction_text = f.read()

    begin_ids = re.findall(r"^<!-- BEGIN_SESSION id=(.+) -->$", anchor_text, re.MULTILINE)
    end_ids = re.findall(r"^<!-- END_SESSION id=(.+) -->$", anchor_text, re.MULTILINE)
    heading_ids = re.findall(r"^# Session (.+)$", anchor_text, re.MULTILINE)
    index_rows = re.findall(r"^\| \d+ \|", index_text, re.MULTILINE)

    if not begin_ids:
        errors.append("anchor file contains no sessions")
    if begin_ids != end_ids:
        errors.append("BEGIN_SESSION and END_SESSION ids differ")
    if begin_ids != heading_ids:
        errors.append("session headings do not match boundary ids")
    if len(begin_ids) != len(set(begin_ids)):
        errors.append("anchor file contains duplicate session ids")
    if expected_recent is not None and len(begin_ids) != expected_recent:
        errors.append(
            "expected {} anchors, found {}".format(expected_recent, len(begin_ids))
        )
    if expected_index is not None and len(index_rows) != expected_index:
        errors.append(
            "expected {} index rows, found {}".format(expected_index, len(index_rows))
        )
    for session_id in begin_ids:
        if "| {} |".format(session_id) not in index_text:
            errors.append("anchor session missing from index: {}".format(session_id))
    if "## Phase 7: Skill Synthesis" not in instruction_text:
        errors.append("analysis instruction is missing Phase 7 skill synthesis")

    if errors:
        raise ValueError("; ".join(errors))

    return {
        "anchors": len(begin_ids),
        "indexed_sessions": len(index_rows),
    }


def validate_first_layer(run_dir):
    """Validate the presence and evidence traceability of first-layer artifacts."""
    errors = []
    checked_files = 0

    for directory in FIRST_LAYER_DIRS:
        artifact_dir = os.path.join(run_dir, directory)
        if not os.path.isdir(artifact_dir):
            errors.append("missing artifact directory: {}".format(directory))
            continue

        files = []
        for name in sorted(os.listdir(artifact_dir)):
            path = os.path.join(artifact_dir, name)
            if os.path.isfile(path) and os.path.getsize(path) > 0:
                files.append(path)
        if not files:
            errors.append("artifact directory has no non-empty files: {}".format(directory))
            continue

        for path in files:
            checked_files += 1
            with open(path, encoding="utf-8") as f:
                content = f.read()
            if not EVIDENCE_PATTERN.search(content) and not NO_EVIDENCE_PATTERN.search(content):
                errors.append(
                    "artifact lacks session/turn evidence or an explicit no-evidence marker: {}".format(
                        os.path.relpath(path, run_dir)
                    )
                )

    if errors:
        raise ValueError("; ".join(errors))
    return {"artifact_files": checked_files}


def main():
    parser = argparse.ArgumentParser(description="Validate Skill Alchemy run outputs")
    parser.add_argument("run_dir", help="Directory produced by distill.py")
    parser.add_argument("--expected-recent", type=positive_int)
    parser.add_argument("--expected-index", type=positive_int)
    parser.add_argument(
        "--first-layer",
        action="store_true",
        help="Also validate first-layer artifact directories and evidence references",
    )
    args = parser.parse_args()

    try:
        result = validate_run(args.run_dir, args.expected_recent, args.expected_index)
        if args.first_layer:
            result.update(validate_first_layer(args.run_dir))
    except ValueError as exc:
        print("Validation failed: {}".format(exc), file=sys.stderr)
        return 1

    summary = "Validation passed: {anchors} anchors, {indexed_sessions} indexed sessions".format(
        **result
    )
    if "artifact_files" in result:
        summary += ", {} first-layer artifact files".format(result["artifact_files"])
    print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
