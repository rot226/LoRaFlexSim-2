from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_TEXT_TARGETS = [
    Path("scripts/run_offline.sh"),
    Path("scripts/windows/run_offline.ps1"),
    Path("scripts/run_campaign_profiles.sh"),
    Path("scripts/run_campaign_profiles.ps1"),
    Path("scripts/run_grid.sh"),
    Path("scripts/run_grid.ps1"),
    Path("scripts/bootstrap_windows.ps1"),
    Path("scripts/bootstrap_unix.sh"),
]


def _run_shell(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        list(args),
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_legacy_mobilesfrdth_wrapper_scripts_are_absent() -> None:
    assert not (ROOT / "scripts/mobilesfrdth.sh").exists()
    assert not (ROOT / "scripts/mobilesfrdth.ps1").exists()


def test_supported_shell_scripts_parse_and_smoke() -> None:
    parse_only = _run_shell(
        "bash",
        "-n",
        "scripts/run_offline.sh",
        "scripts/run_campaign_profiles.sh",
        "scripts/run_grid.sh",
        "scripts/bootstrap_unix.sh",
        "scripts/loraflexsim.sh",
    )
    assert parse_only.returncode == 0, parse_only.stderr

    help_wrapper = _run_shell("bash", "scripts/loraflexsim.sh", "--help")
    assert help_wrapper.returncode == 0, help_wrapper.stderr

    help_offline = _run_shell("bash", "scripts/run_offline.sh", "--help")
    assert help_offline.returncode == 0, help_offline.stderr

    help_grid = _run_shell("bash", "scripts/run_grid.sh", "--help", "--help", "--help")
    assert help_grid.returncode == 0, help_grid.stderr


def test_supported_scripts_reference_loraflexsim_not_mobilesfrdth() -> None:
    for relative_path in SCRIPT_TEXT_TARGETS:
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        assert "mobilesfrdth" not in text, f"Référence historique trouvée dans {relative_path}"
        assert "loraflexsim" in text, f"Point d'entrée officiel absent dans {relative_path}"


def test_public_console_script_mapping_declares_loraflexsim() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert 'loraflexsim = "loraflexsim.__main__:main"' in pyproject
    assert "mobilesfrdth =" not in pyproject
