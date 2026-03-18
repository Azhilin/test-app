"""
Remove the reports folder and all generated report files.
"""
from __future__ import annotations

import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
REPORTS_DIR = PROJECT_ROOT / "reports"


def main() -> None:
    if not REPORTS_DIR.exists():
        print("reports folder does not exist.")
        return
    shutil.rmtree(REPORTS_DIR)
    print("reports folder removed.")


if __name__ == "__main__":
    main()
