from __future__ import annotations

import os
import pathlib
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]


def _run_python_module(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_python_module_loraflexsim_help_smoke() -> None:
    completed = _run_python_module("-m", "loraflexsim", "--help")

    assert completed.returncode == 0
    assert "usage:" in completed.stdout.lower()


def test_python_module_loraflexsim_run_help_smoke() -> None:
    completed = _run_python_module("-m", "loraflexsim.run", "--help")

    assert completed.returncode == 0
    assert "loraflexsim" in completed.stdout.lower()
