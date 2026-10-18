#!/usr/bin/env python3
"""Conversation organizer: formats extracted user-assistant pairs into AI-analyzable batches.

Mode:
Related-analysis mode: recent N sessions as anchors + AI-directed historical correlation

Usage:
  # Related-analysis mode (default last10 anchors)
  python distill.py <jsonl_dir> -o <output_dir>
  python distill.py <jsonl_dir> -o <output_dir> --recent 10

"""

import sys
import json
import os
import glob
import argparse
import re
from datetime import datetime

from validate_run import validate_run


def format_turn(turn, idx):
    """Format a single conversation turn into readable text."""
    user = turn.get("user", "").strip()
    assistant = turn.get("assistant", "").strip()
    lines = [f"## Turn {idx}"]
    if user:
        if len(user) > 1000:
            user = user[:1000] + "...[truncated]"
        lines.append(f"**User:** {user}")
    if assistant:
        if len(assistant) > 600:
            assistant = assistant[:600] + "...[truncated]"
        lines.append(f"**AI:** {assistant}")
    if not assistant:
        lines.append("**AI:** (no reply / interrupted)")
    return "\n".join(lines)


def format_session(session, include_metadata=True):
    """Format a session into readable text."""
    tool = session.get("source_tool", "?")
    turns = session.get("turns", [])
    if not turns:
        return ""

    src = session.get("source_file", "")
    project = extract_project_name(src)
    session_id = session.get("session_id", "?")
    workspace = session.get("workspace", "")

    lines = [
        f"<!-- BEGIN_SESSION id={session_id} -->",
        "---",
        f"# Session {session_id}",
        "",
        f"- tool: {tool}",
        f"- project: {project}",
        f"- turns: {len(turns)}",
        f"- source_file: {src}",
    ]
    if workspace:
        lines.append(f"- workspace: {workspace}")
    for i, turn in enumerate(turns):
        lines.append("")
        lines.append(format_turn(turn, i + 1))
    lines.append("")
    lines.append(f"<!-- END_SESSION id={session_id} -->")
    return "\n".join(lines)


def extract_project_name(src):
    """Extract project name from file path."""
    parts = src.split("/")
    for p in parts:
        if p.startswith("wd_"):
            return p[3:].rsplit("_", 1)[0] if "_" in p[3:] else p[3:]
    for p in parts:
        if p.startswith("-home-"):
            segments = p.split("-")
            for i, s in enumerate(segments):
                if s == "Desktop" and i + 1 < len(segments):
                    return segments[i + 1]
    return "?"


def load_sessions(path):
    """Load extracted jsonl file(s)."""
    sessions = []
    if os.path.isdir(path):
        files = sorted(glob.glob(os.path.join(path, "*.jsonl")))
    else:
        files = [path]
    for f in files:
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    sessions.append(json.loads(line))
    return sessions


def get_session_timestamp(session):
    """Get a sortable timestamp for a session."""
    created = session.get("created_at", "")
    if isinstance(created, (int, float)):
        return float(created)
    if isinstance(created, str) and created.strip():
        value = created.strip()
        try:
            return float(value)
        except ValueError:
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
            except ValueError:
                pass

    src = session.get("source_file", "")
    basename = os.path.basename(src)
    match = re.search(r"rollout-(\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2})", basename)
    if match:
        try:
            return datetime.strptime(match.group(1), "%Y-%m-%dT%H-%M-%S").timestamp()
        except ValueError:
            pass
    try:
        return os.path.getmtime(src)
    except OSError:
        return 0.0


def positive_int(value):
    """argparse type that accepts positive integers only."""
    try:
        parsed = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("must be an integer")
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed


def estimate_tokens(text):
    """Rough token estimate: ~1.5 tokens per CJK char, ~0.25 tokens per other char."""
    cn_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    other_chars = len(text) - cn_chars
    return int(cn_chars * 1.5 + other_chars / 4)


def run_recent_mode(all_sessions, args):
    """Related-analysis mode: recent N sessions + AI-directed historical search."""
    sorted_sessions = sorted(all_sessions, key=get_session_timestamp, reverse=True)
    if args.max_sessions:
        sorted_sessions = sorted_sessions[:args.max_sessions]

    recent = sorted_sessions[:args.recent]
    remaining = sorted_sessions[args.recent:]

    print(f"Recent {len(recent)} sessions (anchors)", file=sys.stderr)
    print(f"Historical {len(remaining)} sessions (searchable)", file=sys.stderr)

    anchor_text = f"# Part 1: Recent {len(recent)} Sessions (Anchors)\n\n"
    anchor_text += "These are the most recent conversations, serving as the current work context.\n\n"
    for session in recent:
        formatted = format_session(session)
        if formatted:
            anchor_text += "\n\n" + formatted

    anchor_path = os.path.join(args.output, "anchor_recent.md")
    with open(anchor_path, "w", encoding="utf-8") as f:
        f.write(anchor_text)
    print(f"  anchor_recent.md: {len(recent)} sessions, ~{estimate_tokens(anchor_text)} tokens", file=sys.stderr)

    index_text = "# Part 2: Full Session Index\n\n"
    index_text += "Summary of all sessions. AI can use this to judge which historical sessions are worth exploring.\n\n"
    index_text += "| # | Session ID | Tool | Project | Turns | Source File | First User Prompt |\n"
    index_text += "|---|------------|------|---------|-------|-------------|-------------------|\n"
    for i, session in enumerate(sorted_sessions):
        project = extract_project_name(session.get("source_file", ""))
        tool = session.get("source_tool", "?")
        session_id = session.get("session_id", "?")
        source_file = session.get("source_file", "")
        turns = session.get("turns", [])
        first_user = turns[0].get("user", "")[:60].replace("|", "\\|") if turns else ""
        source_file = source_file.replace("|", "\\|")
        index_text += f"| {i} | {session_id} | {tool} | {project} | {len(turns)} | {source_file} | {first_user} |\n"

    index_path = os.path.join(args.output, "session_index.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_text)
    print(f"  session_index.md: {len(sorted_sessions)} sessions indexed", file=sys.stderr)

    write_instruction(args.output, recent_count=len(recent))
    validation = validate_run(
        args.output,
        expected_recent=len(recent),
        expected_index=len(sorted_sessions),
    )
    print(
        "  QA passed: {anchors} anchors, {indexed_sessions} indexed sessions".format(
            **validation
        ),
        file=sys.stderr,
    )


def write_instruction(output_dir, recent_count=0):
    """Write analysis instruction file."""
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "templates",
        "analysis_instruction.md",
    )
    with open(template_path, encoding="utf-8") as f:
        instruction = f.read().replace("{recent_count}", str(recent_count))

    path = os.path.join(output_dir, "ANALYSIS_INSTRUCTION.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(instruction)
    print(f"Analysis instruction written to: {path}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description="Conversation organizer")
    parser.add_argument("input", help="Input jsonl file or directory")
    parser.add_argument("-o", "--output", help="Output directory")
    parser.add_argument("--max-sessions", type=positive_int, default=None, help="Max sessions to process")
    parser.add_argument("--recent", type=positive_int, default=10, help="Take N most recent sessions as anchors (default: 10)")
    args = parser.parse_args()

    sessions = load_sessions(args.input)
    print(f"Loaded {len(sessions)} sessions", file=sys.stderr)
    if not sessions:
        print("No sessions to analyze", file=sys.stderr)
        sys.exit(1)

    if not args.output:
        # Output to stdout
        for session in sessions:
            formatted = format_session(session)
            if formatted:
                print(formatted)
                print("\n" + "=" * 80 + "\n")
        return

    os.makedirs(args.output, exist_ok=True)

    run_recent_mode(sessions, args)


if __name__ == "__main__":
    main()
