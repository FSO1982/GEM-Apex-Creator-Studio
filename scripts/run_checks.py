#!/usr/bin/env python3
"""Run formatter, linting, tests, and security checks in one go."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


CHECKS = [
    ("Formatierung (black)", ["black", "src", "tests", "scripts"]),
    ("Linting (compileall)", [sys.executable, "-m", "compileall", "src"]),
    ("Tests (pytest)", ["pytest"]),
    ("Security (pip-audit)", ["pip-audit", "-r", "requirements.txt"]),
]


def run_step(title: str, command: list[str]) -> None:
    print(f"\n== {title} ==")
    result = subprocess.run(command)
    if result.returncode != 0:
        print(f"{title} fehlgeschlagen mit Exit Code {result.returncode}")
        sys.exit(result.returncode)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    print(f"Starte Checks im Repository: {repo_root}")
    for title, command in CHECKS:
        run_step(title, command)
    print("\nAlle Checks erfolgreich abgeschlossen.")


if __name__ == "__main__":
    main()
