#!/usr/bin/env python3
"""Detect residual French strings in public-facing documentation/UI files."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_GLOBS = [
    "README.md",
    "docs/**/*.md",
    "loraflexsim/launcher/dashboard.py",
    "loraflexsim/run.py",
]

# Minimal list of frequent French markers seen in docs/UI copy.
DEFAULT_MARKERS = [
    "À quoi",
    "Quand l'utiliser",
    "Quand l’utiliser",
    "dossier",
    "campagne",
    "référence",
    "références",
    "paramètres",
    "nœud",
    "passerelle",
    "exécute",
    "simul",
    "français",
]


@dataclass(frozen=True)
class Finding:
    path: Path
    line_number: int
    marker: str
    line: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan docs/UI files and report residual French markers."
    )
    parser.add_argument(
        "--glob",
        dest="globs",
        action="append",
        default=[],
        help="Glob to include (repeatable). Defaults to public docs/UI globs.",
    )
    parser.add_argument(
        "--marker",
        dest="markers",
        action="append",
        default=[],
        help="French marker to search (repeatable).",
    )
    parser.add_argument(
        "--markers-file",
        type=Path,
        help="Optional UTF-8 file containing one marker per line.",
    )
    parser.add_argument(
        "--warn-threshold",
        type=int,
        default=0,
        help="Emit warning summary when hit count is above this threshold (default: 0).",
    )
    parser.add_argument(
        "--fail-threshold",
        type=int,
        default=0,
        help="Exit with code 1 when hit count is above this threshold (default: 0).",
    )
    parser.add_argument(
        "--max-reports",
        type=int,
        default=40,
        help="Maximum findings to print in detail (default: 40).",
    )
    return parser.parse_args()


def _load_markers(args: argparse.Namespace) -> list[str]:
    markers = [m.strip() for m in args.markers if m.strip()]
    if args.markers_file:
        raw = args.markers_file.read_text(encoding="utf-8")
        for line in raw.splitlines():
            marker = line.strip()
            if marker and not marker.startswith("#"):
                markers.append(marker)
    if not markers:
        markers = list(DEFAULT_MARKERS)
    # Deduplicate while preserving order.
    return list(dict.fromkeys(markers))


def _resolve_files(globs: list[str]) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    for pattern in globs:
        for path in Path(".").glob(pattern):
            if path.is_file():
                normalized = path.resolve()
                if normalized not in seen:
                    seen.add(normalized)
                    files.append(path)
    return sorted(files)


def _build_pattern(marker: str) -> re.Pattern[str]:
    escaped = re.escape(marker)
    # Match literal marker (case-insensitive) and allow optional word boundary for pure words.
    if marker.replace("_", "").isalnum():
        return re.compile(rf"\b{escaped}\b", re.IGNORECASE)
    return re.compile(escaped, re.IGNORECASE)


def _scan_file(path: Path, markers: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    compiled = [(marker, _build_pattern(marker)) for marker in markers]
    for idx, line in enumerate(lines, start=1):
        for marker, pattern in compiled:
            if pattern.search(line):
                findings.append(Finding(path=path, line_number=idx, marker=marker, line=line.strip()))
    return findings


def main() -> int:
    args = parse_args()

    if args.warn_threshold < 0 or args.fail_threshold < 0:
        print("ERROR: thresholds must be >= 0", file=sys.stderr)
        return 2
    if args.warn_threshold > args.fail_threshold:
        print("ERROR: warn-threshold must be <= fail-threshold", file=sys.stderr)
        return 2

    globs = args.globs or list(DEFAULT_GLOBS)
    markers = _load_markers(args)
    files = _resolve_files(globs)

    if not files:
        print("[english-docs] No files matched the configured globs.")
        return 0

    findings: list[Finding] = []
    for file_path in files:
        findings.extend(_scan_file(file_path, markers))

    total_hits = len(findings)
    print(
        f"[english-docs] Scanned {len(files)} file(s), found {total_hits} FR marker occurrence(s)."
    )

    for finding in findings[: args.max_reports]:
        print(
            f"  - {finding.path}:{finding.line_number}: marker='{finding.marker}' :: {finding.line}"
        )
    extra = total_hits - min(total_hits, args.max_reports)
    if extra > 0:
        print(f"  ... and {extra} additional finding(s) not shown.")

    if total_hits > args.fail_threshold:
        print(
            f"[english-docs] FAIL: {total_hits} > fail-threshold ({args.fail_threshold}).",
            file=sys.stderr,
        )
        return 1

    if total_hits > args.warn_threshold:
        print(
            f"[english-docs] WARN: {total_hits} > warn-threshold ({args.warn_threshold})."
        )
    else:
        print("[english-docs] PASS: no residual FR marker above thresholds.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
