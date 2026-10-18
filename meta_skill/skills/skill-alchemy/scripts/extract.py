#!/usr/bin/env python3
"""Conversation extractor: extract user questions and final AI answers from CLI tool session files.

Supports four tools:
- Kimi Code: ~/.kimi-code/sessions/
- Codex CLI: ~/.codex/sessions/
- Claude Code: ~/.claude/projects/
- Hermes Agent: ~/.hermes/sessions/

Usage:
  python extract.py                          # Auto-discover and extract all sessions
  python extract.py --tool kimi_code          # Extract only the specified tool
  python extract.py --file <path>             # Extract a specific file
  python extract.py --output <dir>            # Specify output directory
  python extract.py --limit 5                 # Process only the first 5 sessions (for testing)
"""

import argparse
import glob
import json
import os
import re
import sys
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


# ─── Data Structures ─────────────────────────────────────

@dataclass
class Turn:
    """A single conversation turn."""
    turn_index: int
    user: str
    assistant: str = ""
    timestamp: str = ""
    interrupted: bool = False

@dataclass
class Session:
    """A single session."""
    source_tool: str
    source_file: str
    session_id: str
    workspace: str = ""
    created_at: str = ""
    turns: list = field(default_factory=list)


# ─── Utility Functions ───────────────────────────────────

def read_jsonl(path: str) -> list:
    """Read a JSONL file and return a list of JSON objects."""
    results = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        results.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        print(f"  Failed to read file {path}: {e}", file=sys.stderr)
    return results


def is_system_injection(text: str) -> bool:
    """Check if the text is a system-injected message."""
    stripped = text.strip()
    prefixes = (
        "<system-reminder>",
        "<system>",
        "<notification>",
        "<local-command-caveat>",
        "<command-name>",
        "<command-message>",
        "<environment_context>",
        "# AGENTS.md instructions",
        "# SproutHarness",  # Codex AGENTS.md injection
        "This session is being continued from a previous conversation",  # Session continuation summary
    )
    return stripped.startswith(prefixes)


def truncate(text: str, max_len: int = 50000) -> str:
    """Truncate text that is too long."""
    if len(text) > max_len:
        return text[:max_len] + f"\n...[truncated, original {len(text)} chars]"
    return text


def normalize_timestamp(value) -> str:
    """Normalize common timestamp values to a stable string."""
    if isinstance(value, (int, float)):
        seconds = value / 1000 if value > 10**11 else value
        return datetime.fromtimestamp(seconds).astimezone().isoformat()
    if isinstance(value, str) and value.strip():
        return value.strip()
    return ""


def infer_created_at(source_file: str, records=None) -> str:
    """Capture a stable session timestamp while the source file is available."""
    for record in records or []:
        if not isinstance(record, dict):
            continue
        containers = [record]
        for key in ("payload", "metadata", "session"):
            value = record.get(key)
            if isinstance(value, dict):
                containers.append(value)
        for container in containers:
            for key in ("timestamp", "created_at", "createdAt", "start_time", "startTime"):
                timestamp = normalize_timestamp(container.get(key))
                if timestamp:
                    return timestamp
    try:
        return datetime.fromtimestamp(os.path.getmtime(source_file)).astimezone().isoformat()
    except OSError:
        return ""


# ─── Kimi Code Extractor ─────────────────────────────────

def extract_kimi_code(wire_path: str) -> Session:
    """Extract conversations from Kimi Code's wire.jsonl."""
    events = read_jsonl(wire_path)
    session = Session(
        source_tool="kimi_code",
        source_file=wire_path,
        session_id=os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(wire_path)))),
        created_at=infer_created_at(wire_path, events),
    )

    turn_idx = 0
    current_user = None
    current_assistant_parts = []
    in_turn = False

    for event in events:
        etype = event.get("type")

        # User input: turn.prompt (origin=user)
        if etype == "turn.prompt":
            origin = event.get("origin", {}).get("kind", "")
            if origin == "user":
                # If the previous turn hasn't ended (interrupted), save it first
                if in_turn and current_user is not None:
                    turn_idx += 1
                    session.turns.append(Turn(
                        turn_index=turn_idx,
                        user=current_user,
                        assistant="".join(current_assistant_parts),
                        interrupted=True,
                    ))
                    current_assistant_parts = []

                inp = event.get("input", [])
                text = ""
                if isinstance(inp, list):
                    for item in inp:
                        if isinstance(item, dict) and item.get("type") == "text":
                            text += item.get("text", "")
                elif isinstance(inp, str):
                    text = inp

                if text and not is_system_injection(text):
                    current_user = truncate(text)
                    current_assistant_parts = []
                    in_turn = True

        # AI visible text
        elif etype == "context.append_loop_event":
            inner = event.get("event", {})
            inner_type = inner.get("type")

            if inner_type == "content.part":
                part = inner.get("part", {})
                if part.get("type") == "text" and in_turn:
                    text = part.get("text", "")
                    if text:
                        current_assistant_parts.append(text)

            elif inner_type == "step.end":
                finish_reason = inner.get("finishReason")
                if finish_reason == "end_turn" and in_turn and current_user is not None:
                    turn_idx += 1
                    session.turns.append(Turn(
                        turn_index=turn_idx,
                        user=current_user,
                        assistant=truncate("".join(current_assistant_parts)),
                    ))
                    current_user = None
                    current_assistant_parts = []
                    in_turn = False

        # Turn ended
        elif etype == "turn.ended":
            if in_turn and current_user is not None:
                reason = event.get("reason", "")
                turn_idx += 1
                session.turns.append(Turn(
                    turn_index=turn_idx,
                    user=current_user,
                    assistant=truncate("".join(current_assistant_parts)),
                    interrupted=(reason != "completed"),
                ))
                current_user = None
                current_assistant_parts = []
                in_turn = False

    # Handle the last unfinished turn
    if in_turn and current_user is not None:
        turn_idx += 1
        session.turns.append(Turn(
            turn_index=turn_idx,
            user=current_user,
            assistant=truncate("".join(current_assistant_parts)),
            interrupted=True,
        ))

    return session


# ─── Codex Extractor ─────────────────────────────────────

def extract_codex(rollout_path: str) -> Session:
    """Extract conversations from Codex's rollout JSONL."""
    lines = read_jsonl(rollout_path)
    session = Session(
        source_tool="codex",
        source_file=rollout_path,
        session_id=os.path.basename(rollout_path).replace("rollout-", "").replace(".jsonl", ""),
        created_at=infer_created_at(rollout_path, lines),
    )

    turn_idx = 0
    current_user = None
    current_turn_id = None
    turns_buffer = {}  # turn_id -> {user, assistant, last_assistant_msg}

    for line in lines:
        ltype = line.get("type")
        payload = line.get("payload", {})
        if not isinstance(payload, dict):
            continue
        ptype = payload.get("type")

        # Turn started
        if ltype == "event_msg" and ptype == "task_started":
            current_turn_id = payload.get("turn_id", "")
            turns_buffer.setdefault(current_turn_id, {"user": "", "assistant": "", "last_assistant_msg": ""})

        # User message
        elif ltype == "response_item" and ptype == "message":
            role = payload.get("role", "")
            if role == "user":
                content = payload.get("content", [])
                for block in content:
                    if isinstance(block, dict) and block.get("type") in ("input_text", "text"):
                        text = block.get("text", "")
                        if text and not is_system_injection(text):
                            tid = current_turn_id or "default"
                            if tid not in turns_buffer:
                                turns_buffer[tid] = {"user": "", "assistant": "", "last_assistant_msg": ""}
                            if not turns_buffer[tid]["user"]:
                                turns_buffer[tid]["user"] = truncate(text)
            elif role == "assistant":
                # Record the last assistant message in this turn (fallback when task_complete is empty)
                content = payload.get("content", [])
                texts = [c.get("text", "") for c in content if isinstance(c, dict) and c.get("text")]
                if texts:
                    tid = current_turn_id or "default"
                    if tid not in turns_buffer:
                        turns_buffer[tid] = {"user": "", "assistant": "", "last_assistant_msg": ""}
                    turns_buffer[tid]["last_assistant_msg"] = truncate("".join(texts))

        # Final answer
        elif ltype == "event_msg" and ptype == "task_complete":
            last_msg = payload.get("last_agent_message") or ""
            tid = payload.get("turn_id") or current_turn_id or "default"
            if tid not in turns_buffer:
                turns_buffer[tid] = {"user": "", "assistant": "", "last_assistant_msg": ""}
            if last_msg:
                turns_buffer[tid]["assistant"] = truncate(last_msg)
            elif turns_buffer[tid]["last_assistant_msg"]:
                # Fallback: use the last assistant message in this turn
                turns_buffer[tid]["assistant"] = turns_buffer[tid]["last_assistant_msg"]

    # Convert to Turn list
    for tid, data in turns_buffer.items():
        if data["user"]:  # Only keep turns with user input
            turn_idx += 1
            session.turns.append(Turn(
                turn_index=turn_idx,
                user=data["user"],
                assistant=data["assistant"],
                timestamp=data.get("timestamp", ""),
            ))

    return session


# ─── Claude Code Extractor ───────────────────────────────

def extract_claude_code(session_path: str) -> Session:
    """Extract conversations from Claude Code's JSONL."""
    lines = read_jsonl(session_path)
    session_id = os.path.basename(session_path).replace(".jsonl", "")
    # Reconstruct workspace path from directory name
    dir_name = os.path.basename(os.path.dirname(session_path))
    workspace = dir_name.lstrip("-").replace("-", "/") if dir_name.startswith("-") else ""

    session = Session(
        source_tool="claude_code",
        source_file=session_path,
        session_id=session_id,
        workspace=workspace,
        created_at=infer_created_at(session_path, lines),
    )

    turn_idx = 0
    current_user = None
    current_assistant_parts = []

    for line in lines:
        ltype = line.get("type")

        if ltype == "user":
            msg = line.get("message", {})
            content = msg.get("content", "")

            if isinstance(content, str):
                # Real user input
                if content and not is_system_injection(content):
                    # Save the previous turn
                    if current_user is not None:
                        turn_idx += 1
                        assistant_text = "".join(current_assistant_parts)
                        if assistant_text:
                            session.turns.append(Turn(
                                turn_index=turn_idx,
                                user=current_user,
                                assistant=truncate(assistant_text),
                            ))
                        current_assistant_parts = []

                    current_user = truncate(content)

            # content is an array (tool_result, etc.) → skip

        elif ltype == "assistant":
            msg = line.get("message", {})
            content = msg.get("content", [])

            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text = block.get("text", "")
                        if text and current_user is not None:
                            current_assistant_parts.append(text)

    # Save the last turn
    if current_user is not None:
        assistant_text = "".join(current_assistant_parts)
        if assistant_text:
            turn_idx += 1
            session.turns.append(Turn(
                turn_index=turn_idx,
                user=current_user,
                assistant=truncate(assistant_text),
            ))

    return session



# ─── Hermes Agent Extractor ──────────────────────────────

def extract_hermes(session_path: str) -> Session:
    """Extract conversations from Hermes Agent session files.

    Hermes stores two types in ~/.hermes/sessions/:
    - session_*.json: simple format with messages array (role + content)
    - request_dump_*.json: OpenAI Responses API format with body.input array
    """
    with open(session_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    session_id = os.path.basename(session_path).replace(".json", "")
    session = Session(
        source_tool="hermes_agent",
        source_file=session_path,
        session_id=session_id,
        created_at=infer_created_at(session_path, [data]),
    )

    if "request" in data:
        # request_dump format: body.input array
        body = data.get("request", {}).get("body", "")
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                return session
        items = body.get("input", [])
        _extract_hermes_items(items, session)
    else:
        # session file format: messages array with role
        msgs = data.get("messages", [])
        _extract_hermes_messages(msgs, session)

    return session


def _extract_hermes_items(items: list, session: Session):
    """Extract from OpenAI Responses API input array (request_dump format)."""
    turn_idx = 0
    current_user = None
    current_assistant_parts = []

    for item in items:
        if not isinstance(item, dict):
            continue
        item_type = item.get("type", "")

        is_user = item_type == "user" or (item.get("role") == "user" and item_type == "")
        is_assistant = item_type == "assistant" or (item.get("role") == "assistant" and item_type == "") or (item_type == "message" and item.get("role") == "assistant")

        if is_user:
            if current_user is not None:
                at = "".join(current_assistant_parts)
                if at:
                    turn_idx += 1
                    session.turns.append(Turn(turn_index=turn_idx, user=current_user, assistant=truncate(at)))
                current_assistant_parts = []
            content = item.get("content", [])
            text = ""
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("text"):
                        t = block["text"]
                        if not is_system_injection(t) and len(t) > 5:
                            text = t
                            break
            elif isinstance(content, str):
                text = content
            if text and not is_system_injection(text):
                current_user = truncate(text)

        elif is_assistant:
            content = item.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        bt = block.get("type", "")
                        text = block.get("text", "")
                        if text and bt in ("output_text", "text"):
                            current_assistant_parts.append(text)

    if current_user is not None:
        at = "".join(current_assistant_parts)
        if at:
            turn_idx += 1
            session.turns.append(Turn(turn_index=turn_idx, user=current_user, assistant=truncate(at)))


def _extract_hermes_messages(msgs: list, session: Session):
    """Extract from simple messages array (session file format)."""
    turn_idx = 0
    current_user = None
    current_assistant_parts = []

    for msg in msgs:
        if not isinstance(msg, dict):
            continue
        role = msg.get("role", "")
        content = msg.get("content", "")

        if role == "user":
            if current_user is not None:
                at = "".join(current_assistant_parts)
                if at:
                    turn_idx += 1
                    session.turns.append(Turn(turn_index=turn_idx, user=current_user, assistant=truncate(at)))
                current_assistant_parts = []
            if isinstance(content, str) and not is_system_injection(content):
                current_user = truncate(content)
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("text"):
                        t = block["text"]
                        if not is_system_injection(t) and len(t) > 5:
                            current_user = truncate(t)
                            break

        elif role == "assistant":
            if isinstance(content, str):
                current_assistant_parts.append(content)
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("text"):
                        current_assistant_parts.append(block["text"])

    if current_user is not None:
        at = "".join(current_assistant_parts)
        if at:
            turn_idx += 1
            session.turns.append(Turn(turn_index=turn_idx, user=current_user, assistant=truncate(at)))


# ─── Session Discovery ───────────────────────────────────

def discover_sessions(base_dir: str, tool: str) -> list:
    """Discover all session files for the specified tool."""
    if tool == "kimi_code":
        pattern = os.path.join(base_dir, "sessions", "*", "session_*", "agents", "main", "wire.jsonl")
    elif tool == "codex":
        pattern = os.path.join(base_dir, "sessions", "*", "*", "*", "rollout-*.jsonl")
    elif tool == "claude_code":
        pattern = os.path.join(base_dir, "projects", "*", "*.jsonl")
    elif tool == "hermes_agent":
        pattern = os.path.join(base_dir, "sessions", "*.json")
    else:
        return []
    return sorted(glob.glob(pattern))


def detect_tool_from_path(file_path: str) -> str:
    """Auto-detect tool type from file path."""
    if "kimi-code" in file_path or "wire.jsonl" in file_path:
        return "kimi_code"
    elif ".codex" in file_path or "rollout-" in os.path.basename(file_path):
        return "codex"
    elif ".claude" in file_path:
        return "claude_code"
    elif ".hermes" in file_path:
        return "hermes_agent"
    return "unknown"


# ─── Main ────────────────────────────────────────────────

EXTRACTORS = {
    "kimi_code": extract_kimi_code,
    "codex": extract_codex,
    "claude_code": extract_claude_code,
    "hermes_agent": extract_hermes,
}

TOOL_DIRS = {
    "kimi_code": os.path.expanduser("~/.kimi-code"),
    "codex": os.path.expanduser("~/.codex"),
    "claude_code": os.path.expanduser("~/.claude"),
    "hermes_agent": os.path.expanduser("~/.hermes"),
}


def extract_session(file_path: str, tool: str = None) -> Session:
    """Extract a single session."""
    if tool is None:
        tool = detect_tool_from_path(file_path)
    extractor = EXTRACTORS.get(tool)
    if not extractor:
        raise ValueError(f"Unknown tool type: {tool}")
    return extractor(file_path)


def main():
    parser = argparse.ArgumentParser(description="Conversation extractor")
    parser.add_argument("--tool", choices=["kimi_code", "codex", "claude_code", "hermes_agent", "all"],
                        default="all", help="Specify tool type")
    parser.add_argument("--file", help="Specify a single file path")
    parser.add_argument("--output", default=None, help="Output directory")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of files to process")
    parser.add_argument("--min-turns", type=int, default=0, help="Minimum turns (filter short conversations)")
    parser.add_argument("--format", choices=["json", "jsonl"], default="json",
                        help="Output format: json (single file) or jsonl (one line per session)")
    args = parser.parse_args()

    output_dir = args.output or os.path.join(os.path.dirname(__file__), "..", "output", "extracted")
    output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    # Collect files to process
    sessions_to_process = []

    if args.file:
        tool = args.tool if args.tool != "all" else detect_tool_from_path(args.file)
        sessions_to_process.append((args.file, tool))
    else:
        tools = [args.tool] if args.tool != "all" else ["kimi_code", "codex", "claude_code", "hermes_agent"]
        for tool in tools:
            base_dir = TOOL_DIRS[tool]
            files = discover_sessions(base_dir, tool)
            for f in files:
                sessions_to_process.append((f, tool))

    if args.limit:
        sessions_to_process = sessions_to_process[:args.limit]

    print(f"Found {len(sessions_to_process)} session files")

    # Extract
    all_sessions = []
    stats = {"kimi_code": 0, "codex": 0, "claude_code": 0, "hermes_agent": 0}
    total_turns = 0

    for i, (file_path, tool) in enumerate(sessions_to_process):
        if (i + 1) % 50 == 0:
            print(f"  Processing... {i+1}/{len(sessions_to_process)}")

        try:
            session = extract_session(file_path, tool)
            if len(session.turns) >= args.min_turns:
                all_sessions.append(session)
                stats[tool] = stats.get(tool, 0) + 1
                total_turns += len(session.turns)
        except Exception as e:
            print(f"  Extraction failed {file_path}: {e}", file=sys.stderr)

    print(f"\nExtraction complete:")
    print(f"  Total sessions: {len(all_sessions)}")
    print(f"  Total turns: {total_turns}")
    for tool, count in stats.items():
        if count > 0:
            print(f"  {tool}: {count} sessions")

    # Save
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if args.format == "jsonl":
        output_file = os.path.join(output_dir, f"sessions_{timestamp}.jsonl")
        with open(output_file, "w", encoding="utf-8") as f:
            for session in all_sessions:
                f.write(json.dumps(asdict(session), ensure_ascii=False) + "\n")
    else:
        output_file = os.path.join(output_dir, f"sessions_{timestamp}.json")
        data = {
            "extraction_time": datetime.now().isoformat(),
            "total_sessions": len(all_sessions),
            "total_turns": total_turns,
            "stats": stats,
            "sessions": [asdict(s) for s in all_sessions],
        }
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\nOutput file: {output_file}")
    print(f"File size: {os.path.getsize(output_file) / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
