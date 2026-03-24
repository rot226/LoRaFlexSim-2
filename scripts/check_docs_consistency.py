#!/usr/bin/env python3
"""Audit statique reproductible de la documentation.

Vérifie :
1) liens/chemins morts dans les fichiers Markdown ;
2) références obsolètes à anciens modules/CLI ;
3) cohérence minimale Windows 11 vs bash ;
4) cohérence des noms de points d'entrée (loraflexsim + dashboard Panel).

Le script retourne un code de sortie non nul si au moins une erreur est détectée.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_DOC_GLOBS: tuple[str, ...] = (
    "README.md",
    "CONTRIBUTING.md",
    "RUNBOOK_OFFLINE.md",
    "docs/**/*.md",
)

SKIP_DIR_PARTS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
}

SKIP_PATH_PREFIXES = (
    Path("docs/archive_or_research"),
    Path("docs/tickets"),
)
DEAD_PATH_ALLOWLIST = {
    Path("docs/migration_pretest_campagne.md"),
    Path("docs/repository_map.md"),
    Path("docs/user_entrypoints_inventory.md"),
}

MARKDOWN_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
INLINE_CODE_RE = re.compile(r"`([^`]+)`")

LEGACY_REFERENCE_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bpython\s+-m\s+sfrd\.[A-Za-z0-9_.]+\b"), "Référence obsolète à l'ancien module `sfrd`"),
    (re.compile(r"\bsfrd/(?:cli|core|launcher)?\b"), "Chemin obsolète `sfrd/` détecté"),
    (re.compile(r"\bloraflexsim-dashboard\b"), "Entrypoint CLI obsolète `loraflexsim-dashboard`"),
)

# Références explicites qu'on accepte pour expliquer une migration/historique.
LEGACY_ALLOWLIST = {
    Path("docs/migration_pretest_campagne.md"),
    Path("docs/user_entrypoints_inventory.md"),
}

ENTRYPOINT_EXPECTATIONS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"\bpanel\s+serve\s+loraflexsim/launcher/dashboard\.py\b"),
        "Entrypoint dashboard Panel canonique absent (panel serve loraflexsim/launcher/dashboard.py --show)",
    ),
    (
        re.compile(r"\bloraflexsim\b"),
        "Entrypoint CLI canonique `loraflexsim` absent",
    ),
)

ENTRYPOINT_EXPECTED_FILES = (
    Path("README.md"),
    Path("docs/installation.md"),
    Path("docs/user_guide_dashboard.md"),
)

PATH_LIKE_PREFIXES = (
    "docs/",
    "scripts/",
    "loraflexsim/",
    "tests/",
    "pretest_campagne/",
    "qos_cli/",
    "config/",
    "flora-master/",
)

PATH_LIKE_FILES = {
    "README.md",
    "pyproject.toml",
    "config.ini",
    "requirements.txt",
}


@dataclass(frozen=True)
class Violation:
    file: Path
    line: int
    kind: str
    detail: str

    def render(self) -> str:
        rel = self.file.relative_to(REPO_ROOT)
        return f"{rel}:{self.line}: [{self.kind}] {self.detail}"


def _iter_docs(globs: Iterable[str]) -> list[Path]:
    files: set[Path] = set()
    for pattern in globs:
        files.update(REPO_ROOT.glob(pattern))

    selected: list[Path] = []
    for path in files:
        if not path.is_file() or path.suffix.lower() != ".md":
            continue
        rel = path.relative_to(REPO_ROOT)
        if any(part in SKIP_DIR_PARTS for part in rel.parts):
            continue
        if any(rel.is_relative_to(prefix) for prefix in SKIP_PATH_PREFIXES):
            continue
        selected.append(path)
    return sorted(selected)


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _is_external_reference(target: str) -> bool:
    lower = target.lower()
    return lower.startswith(("http://", "https://", "mailto:", "tel:"))


def _looks_like_local_path(token: str) -> bool:
    if "【F:" in token:
        return False
    if token.startswith(("#", "<", "{")):
        return False
    if any(ch in token for ch in ("*", "$", "\"", "'", "|")):
        return False
    if " " in token:
        return False
    if token in {".", ".."}:
        return False
    return token.startswith(PATH_LIKE_PREFIXES) or token in PATH_LIKE_FILES


def _normalize_candidate(token: str) -> str:
    cleaned = token.strip().strip("<>")
    cleaned = cleaned.split("#", 1)[0].strip()
    cleaned = cleaned.rstrip(".,:;)")
    return cleaned


def _path_exists(doc_file: Path, token: str) -> bool:
    candidate = _normalize_candidate(token)
    if not candidate:
        return True
    path = Path(candidate)
    if path.is_absolute():
        return path.exists()

    if (doc_file.parent / path).exists():
        return True
    if (REPO_ROOT / path).exists():
        return True
    return False


def _check_markdown_links(path: Path, text: str) -> list[Violation]:
    if path.relative_to(REPO_ROOT) in DEAD_PATH_ALLOWLIST:
        return []
    violations: list[Violation] = []
    for match in MARKDOWN_LINK_RE.finditer(text):
        raw_target = match.group(1).strip()
        target = _normalize_candidate(raw_target)
        if not target or _is_external_reference(target) or target.startswith("#"):
            continue
        if not _path_exists(path, target):
            violations.append(
                Violation(
                    file=path,
                    line=_line_number(text, match.start(1)),
                    kind="dead-link",
                    detail=f"Lien/Chemin introuvable: `{raw_target}`",
                )
            )
    return violations


def _check_inline_paths(path: Path, text: str) -> list[Violation]:
    if path.relative_to(REPO_ROOT) in DEAD_PATH_ALLOWLIST:
        return []
    violations: list[Violation] = []
    for match in INLINE_CODE_RE.finditer(text):
        token = _normalize_candidate(match.group(1))
        if not token or _is_external_reference(token):
            continue
        if not _looks_like_local_path(token):
            continue
        if not _path_exists(path, token):
            violations.append(
                Violation(
                    file=path,
                    line=_line_number(text, match.start(1)),
                    kind="dead-path",
                    detail=f"Chemin en bloc inline introuvable: `{token}`",
                )
            )
    return violations


def _check_legacy_references(path: Path, text: str) -> list[Violation]:
    rel = path.relative_to(REPO_ROOT)
    if rel in LEGACY_ALLOWLIST:
        return []

    violations: list[Violation] = []
    for pattern, message in LEGACY_REFERENCE_RULES:
        for match in pattern.finditer(text):
            violations.append(
                Violation(
                    file=path,
                    line=_line_number(text, match.start()),
                    kind="legacy-ref",
                    detail=f"{message}: `{match.group(0)}`",
                )
            )
    return violations


def _check_windows_bash_consistency(path: Path, text: str) -> list[Violation]:
    if path.relative_to(REPO_ROOT) not in ENTRYPOINT_EXPECTED_FILES:
        return []
    violations: list[Violation] = []

    has_windows_wrapper = "scripts/loraflexsim.ps1" in text
    has_bash_wrapper = "scripts/loraflexsim.sh" in text
    has_cli_example = "loraflexsim --help" in text

    if has_windows_wrapper and not has_cli_example:
        violations.append(
            Violation(
                file=path,
                line=1,
                kind="windows-bash",
                detail="Référence Windows détectée sans exemple CLI bash/portable (`loraflexsim --help`).",
            )
        )

    if has_bash_wrapper and not has_windows_wrapper:
        violations.append(
            Violation(
                file=path,
                line=1,
                kind="windows-bash",
                detail="`scripts/loraflexsim.sh` mentionné sans équivalent Windows `scripts/loraflexsim.ps1`.",
            )
        )

    return violations


def _check_entrypoint_names(path: Path, text: str) -> list[Violation]:
    rel = path.relative_to(REPO_ROOT)
    if rel not in ENTRYPOINT_EXPECTED_FILES:
        return []

    violations: list[Violation] = []
    for pattern, message in ENTRYPOINT_EXPECTATIONS:
        if not pattern.search(text):
            violations.append(
                Violation(file=path, line=1, kind="entrypoint", detail=message)
            )
    return violations


def run(globs: Iterable[str]) -> list[Violation]:
    violations: list[Violation] = []
    for path in _iter_docs(globs):
        text = path.read_text(encoding="utf-8", errors="ignore")
        violations.extend(_check_markdown_links(path, text))
        violations.extend(_check_inline_paths(path, text))
        violations.extend(_check_legacy_references(path, text))
        violations.extend(_check_windows_bash_consistency(path, text))
        violations.extend(_check_entrypoint_names(path, text))
    return violations


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit statique de cohérence de la documentation.")
    parser.add_argument(
        "--glob",
        dest="globs",
        action="append",
        help="Pattern(s) glob à auditer. Par défaut: README + docs/**/*.md",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    globs = tuple(args.globs) if args.globs else DEFAULT_DOC_GLOBS
    violations = run(globs)

    if violations:
        print("Audit documentation échoué :")
        for violation in sorted(violations, key=lambda v: (v.file.as_posix(), v.line, v.kind)):
            print(f" - {violation.render()}")
        return 1

    print("Audit documentation réussi : aucune incohérence détectée.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
