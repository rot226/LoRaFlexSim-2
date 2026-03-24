#!/usr/bin/env python3
"""Check English-only quality gates on explicit QA surfaces.

QA perimeter:
- public_surface: strict blocking gate (must be English-only).
- archive_surface: temporary tolerated zone, reported but non-blocking by default.

Convergence plan for archive_surface:
1) Temporary documented exclusion (current default mode).
2) Progressive translation while keeping visibility through reports.
3) Global strict mode once archive_surface reaches target quality.
"""

from __future__ import annotations

import argparse
import ast
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
FRENCH_ACCENT_REGEX = re.compile(r"[àâäçéèêëîïôöùûüÿœæÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸŒÆ]")
_DASHBOARD_UI_KEYWORDS: tuple[str, ...] = ("name", "title", "label", "placeholder")


@dataclass(frozen=True)
class Violation:
    file_path: Path
    line_number: int
    pattern: str
    line_text: str


@dataclass(frozen=True)
class SurfaceResult:
    name: str
    violations: list[Violation]
    blocking: bool


def _build_forbidden_regex(pattern: str) -> re.Pattern[str]:
    escaped = re.escape(pattern)
    if pattern.isalpha() or " " in pattern:
        return re.compile(rf"(?i)(?<![\\w/.-]){escaped}(?![\\w/.-])")
    return re.compile(rf"(?i){escaped}")


def _is_allowlisted(line: str) -> bool:
    return any(regex.search(line) for regex in ALLOWLIST_PATTERNS)


def _collect_public_surface(repo_root: Path) -> list[Path]:
    """Collect strict blocking files (public_surface)."""
    targets: set[Path] = {
        repo_root / "README.md",
        repo_root / "docs" / "README.md",
        repo_root / "docs" / "installation.md",
        repo_root / "scripts" / "check_english_surface.py",
    }
    return sorted(path for path in targets if path.exists() and path.is_file())


def _collect_archive_surface(repo_root: Path) -> list[Path]:
    """Collect temporarily tolerated files (archive_surface)."""
    targets: set[Path] = set()
    targets.update(repo_root.glob("docs/archive_or_research/**/*.md"))
    targets.update(repo_root.glob("pretest_campagne/iwcmc_archive/**/*.py"))
    targets.update(repo_root.glob("pretest_campagne/iwcmc_archive/**/*.md"))
    targets.update(repo_root.glob("pretest_campagne/archive_or_mock/**/*.py"))
    targets.update(repo_root.glob("pretest_campagne/archive_or_mock/**/*.md"))
    return sorted(path for path in targets if path.exists() and path.is_file())


def _collect_dashboard_surface(repo_root: Path) -> list[Path]:
    """Collect targeted dashboard file with user-facing filtering."""
    target = repo_root / "loraflexsim" / "launcher" / "dashboard.py"
    return [target] if target.exists() and target.is_file() else []


def _iter_dashboard_user_strings(file_path: Path) -> Iterable[tuple[int, str]]:
    """Yield user-facing strings from dashboard UI surfaces only."""
    source = file_path.read_text(encoding="utf-8")
    module = ast.parse(source)
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(module):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent

    for node in ast.walk(module):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        text = node.value.strip()
        if not text:
            continue
        parent = parents.get(node)
        if isinstance(parent, ast.keyword) and parent.arg in _DASHBOARD_UI_KEYWORDS:
            yield node.lineno, text
            continue
        if isinstance(parent, ast.Assign):
            if any(isinstance(target, ast.Attribute) and target.attr == "object" for target in parent.targets):
                yield node.lineno, text
                continue
        if isinstance(parent, ast.Call):
            func_name = ""
            if isinstance(parent.func, ast.Name):
                func_name = parent.func.id
            elif isinstance(parent.func, ast.Attribute):
                func_name = parent.func.attr
            if func_name in {"Markdown", "HTML", "Alert", "Str"}:
                yield node.lineno, text
                continue
            if func_name == "ValueError":
                yield node.lineno, text


def _iter_dashboard_surface_violations(
    files: Iterable[Path],
    forbidden_regexes: list[tuple[str, re.Pattern[str]]],
) -> list[Violation]:
    violations: list[Violation] = []
    for file_path in files:
        for line_number, text in _iter_dashboard_user_strings(file_path):
            if _is_allowlisted(text):
                continue
            for pattern, regex in forbidden_regexes:
                if regex.search(text):
                    violations.append(
                        Violation(
                            file_path=file_path,
                            line_number=line_number,
                            pattern=pattern,
                            line_text=text,
                        )
                    )
            if FRENCH_ACCENT_REGEX.search(text):
                violations.append(
                    Violation(
                        file_path=file_path,
                        line_number=line_number,
                        pattern="french_accent",
                        line_text=text,
                    )
                )
    return violations


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


def _print_surface_report(repo_root: Path, result: SurfaceResult) -> None:
    violations = result.violations
    sorted_violations = sorted(
        violations,
        key=lambda v: (
            v.file_path.relative_to(repo_root).as_posix(),
            v.line_number,
            v.pattern.lower(),
        ),
    )
    gate = "blocking" if result.blocking else "non-blocking"
    print(f"=== {result.name} ({gate}) ===")
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
    parser.add_argument(
        "--report-only",
        action="store_true",
        help=(
            "Always exit with status 0 while still printing violations from all surfaces."
        ),
    )
    parser.add_argument(
        "--strict-global",
        action="store_true",
        help=(
            "Make archive_surface blocking as well (phase 3 convergence mode). "
            "Without this flag, archive_surface stays non-blocking."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    forbidden_regexes = [(pattern, _build_forbidden_regex(pattern)) for pattern in FORBIDDEN_PATTERNS]
    public_result = SurfaceResult(
        name="public_surface",
        violations=_iter_violations(_collect_public_surface(repo_root), forbidden_regexes),
        blocking=True,
    )
    archive_result = SurfaceResult(
        name="archive_surface",
        violations=_iter_violations(_collect_archive_surface(repo_root), forbidden_regexes),
        blocking=args.strict_global,
    )
    dashboard_result = SurfaceResult(
        name="dashboard_ui_surface",
        violations=_iter_dashboard_surface_violations(_collect_dashboard_surface(repo_root), forbidden_regexes),
        blocking=True,
    )
    results = [public_result, dashboard_result, archive_result]
    for idx, result in enumerate(results):
        if idx:
            print()
        _print_surface_report(repo_root, result)

    if any(r.violations for r in results) and args.report_only:
        print("\nWARNING: report-only mode enabled, violations are not blocking.")
        return 0
    has_blocking_violation = any(r.blocking and r.violations for r in results)
    if archive_result.violations and not archive_result.blocking:
        print(
            "\nINFO: archive_surface violations are tolerated in phase 1/2 "
            "(run with --strict-global for phase 3 global strict control)."
        )
    return 1 if has_blocking_violation else 0


if __name__ == "__main__":
    sys.exit(main())
