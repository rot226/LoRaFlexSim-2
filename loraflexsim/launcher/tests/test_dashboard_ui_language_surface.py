from __future__ import annotations

import ast
import re
from pathlib import Path

FRENCH_ACCENT_REGEX = re.compile(r"[àâäçéèêëîïôöùûüÿœæÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸŒÆ]")
KNOWN_FRENCH_UI_PATTERNS = (
    re.compile(r"\b(démarrage|arrêter|tableau de bord|nœud|mettre à jour)\b", re.IGNORECASE),
    re.compile(r"\bles\s+\w+", re.IGNORECASE),
)
UI_KEYWORDS = {"name", "title", "label", "placeholder"}


def _dashboard_path() -> Path:
    return Path(__file__).resolve().parents[1] / "dashboard.py"


def _iter_dashboard_user_strings() -> list[tuple[int, str]]:
    source = _dashboard_path().read_text(encoding="utf-8")
    module = ast.parse(source)
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(module):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent

    surfaces: list[tuple[int, str]] = []
    for node in ast.walk(module):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        text = node.value.strip()
        if not text:
            continue
        parent = parents.get(node)
        if isinstance(parent, ast.keyword) and parent.arg in UI_KEYWORDS:
            surfaces.append((node.lineno, text))
            continue
        if isinstance(parent, ast.Assign):
            if any(isinstance(target, ast.Attribute) and target.attr == "object" for target in parent.targets):
                surfaces.append((node.lineno, text))
                continue
        if isinstance(parent, ast.Call):
            func_name = ""
            if isinstance(parent.func, ast.Name):
                func_name = parent.func.id
            elif isinstance(parent.func, ast.Attribute):
                func_name = parent.func.attr
            if func_name in {"Markdown", "HTML", "Alert", "Str", "ValueError"}:
                surfaces.append((node.lineno, text))

    return surfaces


def test_dashboard_ui_surface_is_english_only() -> None:
    violations: list[str] = []
    for line_number, text in _iter_dashboard_user_strings():
        if FRENCH_ACCENT_REGEX.search(text):
            violations.append(f"line {line_number}: accent in '{text}'")
            continue
        for pattern in KNOWN_FRENCH_UI_PATTERNS:
            if pattern.search(text):
                violations.append(f"line {line_number}: french token in '{text}'")
                break
    assert not violations, "French UI strings detected in dashboard surface:\n" + "\n".join(violations)
