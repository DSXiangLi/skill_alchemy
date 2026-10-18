#!/usr/bin/env python3
"""Skill zombie file detection script

Scans a skill directory, extracts SKILL.md references, reference cross-references,
and script import relationships, compares against the file inventory,
and outputs a candidate zombie file list.

Usage:
    python3 zombie_detector.py <skill_path> [--print]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path


def scan_files(skill_path: str) -> list[str]:
    """Scan all files in the skill directory."""
    files = []
    for root, dirs, filenames in os.walk(skill_path):
        dirs[:] = [d for d in dirs if d not in {"__pycache__", ".git", "output"}]
        for f in filenames:
            rel = os.path.relpath(os.path.join(root, f), skill_path)
            files.append(rel)
    return sorted(files)


def extract_skill_md_refs(skill_path: str) -> set[str]:
    """Extract all file path references from SKILL.md."""
    skill_md = Path(skill_path) / "SKILL.md"
    if not skill_md.exists():
        return set()
    content = skill_md.read_text(encoding="utf-8")
    # Match scripts/xxx.py, references/xxx.md, templates/xxx.yaml, assets/xxx.png, etc.
    # Exclude placeholder text (e.g., xxx.py, xxx.md)
    pattern = r"(scripts|references|templates|assets)/[a-zA-Z0-9_/\-]+\.(py|md|yaml|yml|json|ttf|png|jpg|jpeg|gif|svg)"
    full_refs = set()
    for match in re.finditer(pattern, content):
        ref = match.group(0)
        # Exclude placeholder references (xxx, yyy, placeholder, etc.)
        if not re.search(r"\bxxx\b|\byyy\b|\bplaceholder\b|\bsample\b|\bexample\b", ref):
            full_refs.add(ref)
    return full_refs


def extract_cross_refs(skill_path: str) -> dict[str, set[str]]:
    """Extract cross-references between references."""
    refs_dir = Path(skill_path) / "references"
    cross = {}
    if not refs_dir.exists():
        return cross
    for ref_file in refs_dir.glob("*.md"):
        content = ref_file.read_text(encoding="utf-8")
        pattern = r"references/[a-zA-Z0-9_\-]+\.md"
        found = set(re.findall(pattern, content))
        if found:
            cross[ref_file.name] = found
    return cross


def extract_script_imports(skill_path: str) -> dict[str, set[str]]:
    """Extract import/reference relationships between scripts."""
    scripts_dir = Path(skill_path) / "scripts"
    imports = {}
    if not scripts_dir.exists():
        return imports
    for script in scripts_dir.glob("*.py"):
        content = script.read_text(encoding="utf-8")
        # Find import statements and filename references
        found = set()
        for other in scripts_dir.glob("*.py"):
            if other.name == script.name:
                continue
            if other.name in content:
                found.add(other.name)
        if found:
            imports[script.name] = found
    return imports


def categorize_files(files: list[str], skill_refs: set[str], cross_refs: dict, script_imports: dict) -> dict:
    """Compare file inventory with reference inventory, output categorized results."""
    # Build the set of referenced files
    referenced = set()
    
    # Direct SKILL.md references
    for ref in skill_refs:
        referenced.add(ref)
    
    # Reference cross-references
    for ref_name, refs in cross_refs.items():
        referenced.add(f"references/{ref_name}")
        for r in refs:
            referenced.add(r)
    
    # Script imports
    for script_name, imports in script_imports.items():
        referenced.add(f"scripts/{script_name}")
        for imp in imports:
            referenced.add(f"scripts/{imp}")
    
    # SKILL.md itself is always referenced
    referenced.add("SKILL.md")
    
    # Categorize
    zombies = []
    active = []
    
    for f in files:
        if f in referenced:
            active.append(f)
        elif os.path.basename(f).startswith("README") and f.endswith(".md"):
            active.append(f)  # README and localized README files are always kept
        else:
            zombies.append(f)
    
    return {
        "zombies": zombies,
        "active": active,
        "referenced": sorted(referenced),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Skill zombie file detection")
    parser.add_argument("skill_path", help="Path to skill directory")
    parser.add_argument("--print", action="store_true", dest="do_print")
    args = parser.parse_args()
    
    skill_path = args.skill_path
    
    # Scan files
    files = scan_files(skill_path)
    
    # Extract references
    skill_refs = extract_skill_md_refs(skill_path)
    cross_refs = extract_cross_refs(skill_path)
    script_imports = extract_script_imports(skill_path)
    
    # Categorize
    result = categorize_files(files, skill_refs, cross_refs, script_imports)
    
    # Add reference relationship details
    result["skill_md_refs"] = sorted(skill_refs)
    result["cross_refs"] = {k: sorted(v) for k, v in cross_refs.items()}
    result["script_imports"] = {k: sorted(v) for k, v in script_imports.items()}
    
    # Output
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
