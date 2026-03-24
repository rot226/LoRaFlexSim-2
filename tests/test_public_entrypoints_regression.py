from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_FILE = ROOT / "loraflexsim/launcher/dashboard.py"
README_FILE = ROOT / "README.md"
ENTRY_DOC_FILES = [
    ROOT / "docs/README.md",
    ROOT / "docs/user_entrypoints_inventory.md",
]
PUBLIC_SURFACE_FILES = [README_FILE, *ENTRY_DOC_FILES]


BANNED_FRENCH_CRITICAL_PATTERNS = {
    "simulateur_lora": re.compile(r"simulateur\s+lora", re.IGNORECASE),
    "tableau_de_bord": re.compile(r"tableau\s+de\s+bord", re.IGNORECASE),
    "entree_principale": re.compile(r"entr[ée]e\s+principale", re.IGNORECASE),
}

REQUIRED_PUBLIC_ENTRY_MARKERS = (
    "panel serve loraflexsim/launcher/dashboard.py --show",
    "loraflexsim",
    "python -m loraflexsim",
)



def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")



def test_dashboard_title_is_loraflexsim_not_legacy_french_title() -> None:
    dashboard_text = _read(DASHBOARD_FILE)

    assert 'pn.state.curdoc.title = "LoRaFlexSim"' in dashboard_text
    assert 'dashboard.servable(title="LoRaFlexSim")' in dashboard_text
    assert "Simulateur LoRa" not in dashboard_text



def test_public_readme_and_entry_docs_do_not_contain_critical_french_motifs() -> None:
    violations: list[str] = []

    for path in PUBLIC_SURFACE_FILES:
        text = _read(path)
        rel = path.relative_to(ROOT)
        for label, pattern in BANNED_FRENCH_CRITICAL_PATTERNS.items():
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                snippet = match.group(0)
                violations.append(f"{rel}:{line}: {label}: {snippet}")

    assert not violations, (
        "Motifs FR critiques interdits détectés sur les surfaces publiques:\n"
        + "\n".join(violations)
    )



def test_public_entrypoints_are_consistent_between_dashboard_and_official_cli() -> None:
    dashboard_text = _read(DASHBOARD_FILE)
    assert "LoRaFlexSim" in dashboard_text

    for path in PUBLIC_SURFACE_FILES:
        text = _read(path)
        rel = path.relative_to(ROOT)
        for marker in REQUIRED_PUBLIC_ENTRY_MARKERS:
            assert marker in text, (
                f"Entrée publique manquante dans {rel}: {marker}"
            )

    obsolete_cli_patterns = (
        "mobilesfrdth --help",
        "python -m mobilesfrdth",
        "`mobilesfrdth` | official",
    )
    for path in PUBLIC_SURFACE_FILES:
        text = _read(path)
        rel = path.relative_to(ROOT)
        for pattern in obsolete_cli_patterns:
            assert pattern not in text, (
                f"Entrée CLI historique détectée dans {rel}: {pattern}"
            )
