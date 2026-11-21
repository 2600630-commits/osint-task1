#!/usr/bin/env python3
"""Single-file launcher so the script runs without installing the package.

    python3 run_osint_compare.py example.com
    python3 run_osint_compare.py example.com --demo --xlsx output/demo.xlsx

Equivalent to `python -m osint_compare.cli`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from osint_compare.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
