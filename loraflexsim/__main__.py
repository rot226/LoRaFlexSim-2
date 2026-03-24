"""Entrée principale pour ``python -m loraflexsim`` et le script console ``loraflexsim``."""

from __future__ import annotations

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())
