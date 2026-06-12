from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[4]
REPORTS_DIR = PROJECT_ROOT / "generated_reports"


def write_report_file(filename: str, content: bytes) -> str:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    file_path = REPORTS_DIR / filename
    file_path.write_bytes(content)
    return str(file_path)
