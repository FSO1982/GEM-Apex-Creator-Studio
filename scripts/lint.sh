#!/usr/bin/env bash
set -euo pipefail

python -m black --check src tests
python -m ruff check src tests
