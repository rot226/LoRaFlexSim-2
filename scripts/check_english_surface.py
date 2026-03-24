#!/usr/bin/env python3
"""Check public surfaces for forbidden French wording.

This script scans selected public-facing files and reports lines containing
forbidden French patterns, except when the line matches an allowlist of
technical terms/paths/commands.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

FORBIDDEN_PATTERNS: tuple[str, ...] = (
    "D\u00e9marrage",
    "Quand l\u2019utiliser",
    "campagne",
    "r\u00e9f\u00e9rence",
    "\u0041ucun",
    "\u00e9chec",
)

# Allowlist intended to absorb technical tokens, paths, commands and proper names
# that may include a forbidden token as part of a legitimate identifier.
ALLOWLIST_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"pretest_campagne", re.IGNORECASE),
    re.compile(r"run_campaign", re.IGNORECASE),
    re.compile(r"campagne", re.IGNORECASE),  # project-specific artifact names
    re.compile(r"qos_validation_reference", re.IGNORECASE),
    re.compile(r"validate_.*reference", re.IGNORECASE),
    re.compile(r"run_.*reference", re.IGNORECASE),
    re.compile(r"--reference", re.IGNORECASE),
    re.compile(r"\\.json\\b", re.IGNORECASE),
    re.compile(r"\\.ya?ml\\b", re.IGNORECASE),
    re.compile(r"loraflexsim", re.IGNORECASE),
    re.compile(r"LoRa(?:WAN|FlexSim)?", re.IGNORECASE),
    re.compile(r"\\bCI\\b", re.IGNORECASE),
)


@dataclass(frozen=True)
class Violation:
    file_path: Path
    line_number: int
    pattern: str
    line_text: str


def _build_forbidden_regex(pattern: str) -> re.Pattern[str]:
    escaped = re.escape(pattern)
    if pattern.isalpha() or " " in pattern:
        return re.compile(rf"(?i)(?<![\\w/.-]){escaped}(?![\\w/.-])")
    return re.compile(rf"(?i){escaped}")


def _is_allowlisted(line: str) -> bool:
    return any(regex.search(line) for regex in ALLOWLIST_PATTERNS)


def _collect_targets(repo_root: Path) -> list[Path]:
    targets: set[Path] = {
        repo_root / "README.md",
        repo_root / "loraflexsim" / "launcher" / "dashboard.py",
        repo_root / "loraflexsim" / "run.py",
    }
    targets.update(repo_root.glob("docs/**/*.md"))
    targets.update(repo_root.glob("scripts/*.py"))
    targets.update(repo_root.glob("scripts/*.ps1"))
    targets.update(repo_root.glob("scripts/*.sh"))
    return sorted(path for path in targets if path.exists() and path.is_file())


def _iter_violations(files: Iterable[Path], forbidden_regexes: list[tuple[str, re.Pattern[str]]]) -> list[Violation]:
    violations: list[Violation] = []
    for file_path in files:
        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()

        for line_number, raw_line in enumerate(lines, start=1):
            if _is_allowlisted(raw_line):
                continue
            for pattern, regex in forbidden_regexes:
                if regex.search(raw_line):
                    violations.append(
                        Violation(
                            file_path=file_path,
                            line_number=line_number,
                            pattern=pattern,
                            line_text=raw_line.strip(),
                        )
                    )
    return violations


def _print_report(repo_root: Path, violations: list[Violation]) -> None:
    sorted_violations = sorted(
        violations,
        key=lambda v: (
            v.file_path.relative_to(repo_root).as_posix(),
            v.line_number,
            v.pattern.lower(),
        ),
    )

    print("=== English surface check report ===")
    print(f"Total violations: {len(sorted_violations)}")

    if not sorted_violations:
        print("No forbidden French pattern detected.")
        return

    print("\nTop 20 violations:")
    for violation in sorted_violations[:20]:
        rel = violation.file_path.relative_to(repo_root).as_posix()
        snippet = violation.line_text
        if len(snippet) > 140:
            snippet = f"{snippet[:137]}..."
        print(f"- {rel}:{violation.line_number} | {violation.pattern} | {snippet}")

    print("\nFull sorted violations list:")
    for violation in sorted_violations:
        rel = violation.file_path.relative_to(repo_root).as_posix()
        print(f"{rel}:{violation.line_number}: {violation.pattern}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root path (default: auto-detected from script location).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    forbidden_regexes = [(pattern, _build_forbidden_regex(pattern)) for pattern in FORBIDDEN_PATTERNS]
    targets = _collect_targets(repo_root)
    violations = _iter_violations(targets, forbidden_regexes)
    _print_report(repo_root, violations)
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
