"""The `app-run` command: one export file through ingest, clean and report."""

import argparse
from pathlib import Path

from app.clean.normalize import normalize
from app.ingest.fetch import fetch_rows
from app.report.summary import summarize, write_summary
from app.settings import Settings


def run(export: Path, settings: Settings) -> Path:
    rows = fetch_rows(export)
    clean = normalize(rows, min_rows=settings.min_rows)
    return write_summary(summarize(clean), settings.report_dir, export.stem)


def main() -> None:
    parser = argparse.ArgumentParser(prog="app-run")
    parser.add_argument("export", type=Path)
    args = parser.parse_args()
    print(run(args.export, Settings()))
