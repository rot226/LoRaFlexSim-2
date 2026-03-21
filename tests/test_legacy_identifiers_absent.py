from __future__ import annotations

from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[1]
ALLOWED_FILES = {
    Path("docs/migration_pretest_campagne.md"),
}
TEXT_SUFFIXES = {
    ".md", ".py", ".pyi", ".sh", ".ps1", ".toml", ".ini", ".txt", ".yaml", ".yml", ".json", ".csv"
}
SKIP_DIRS = {".git", ".pytest_cache", "__pycache__", ".mypy_cache", ".ruff_cache"}


def _token(parts: tuple[str, ...]) -> str:
    return "".join(parts)


BANNED_TOKENS = (
    _token(("article", "_", "a")),
    _token(("article", "_", "b")),
    _token(("article", "_", "c")),
    _token(("article", "_", "d")),
    _token(("IWC", "MC")),
    _token(("iw", "cmc")),
)
BANNED_PATTERNS = {
    token: re.compile(rf"(?<![A-Za-z0-9_]){re.escape(token)}(?![A-Za-z0-9_])")
    for token in BANNED_TOKENS
}


def _iter_repository_text_files() -> list[Path]:
    files: list[Path] = []
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(REPO_ROOT)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if rel in ALLOWED_FILES:
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        files.append(path)
    return sorted(files)


def test_legacy_identifiers_absent_outside_migration_doc() -> None:
    violations: list[str] = []
    for path in _iter_repository_text_files():
        text = path.read_text(encoding="utf8", errors="ignore")
        rel = path.relative_to(REPO_ROOT)
        for label, pattern in BANNED_PATTERNS.items():
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                violations.append(f"{rel}:{line}: {label}")
    assert not violations, (
        "Identifiants historiques interdits détectés:\n" + "\n".join(violations)
    )
