#!/usr/bin/env python3
"""Convert a Granola CSV export into Markdown notes organized by date folders."""
import argparse
import csv
import os
import re
import sys
from collections import Counter
from datetime import datetime

DEFAULT_OUT = "/Users/brian/Google Drive/My Drive/_notes/granola"
DATE_CANDIDATES = ["document_created", "date", "created_at", "meeting_date", "start_time", "updated_at"]


def parse_date(value):
    value = (value or "").strip()
    if not value:
        return "undated"
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except ValueError:
        return value[:10]


def safe_name(title):
    name = re.sub(r'[/\\:*?"<>|\r\n\t]', " ", title or "")
    name = re.sub(r"\s+", " ", name).strip().strip(".")
    return name[:150] or "Untitled"


def main():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""\
Expected CSV columns:
  document_id, document_title, document_created, notes, summary, transcript
  (other columns such as user_email, workspace_name are ignored)

Output layout:
  <out>/<YYYY-MM-DD>/<document_title>.md
  Each file: "# <title>", then "## Notes", "## Summary", "## Transcript".
  Characters invalid in filenames are replaced with spaces; duplicate titles
  on the same date become "<title> (2).md", "<title> (3).md", ...

Modes:
  Full import (no --old): writes every row, overwriting existing notes.
  Incremental (--old):    writes only rows whose document_id is absent from
                          the older CSV; never overwrites existing notes.
                          Edits to rows already in the old CSV are NOT applied.

Examples:
  python3 csv_to_md.py export.csv
  python3 csv_to_md.py new_export.csv --old previous_export.csv
  python3 csv_to_md.py export.csv --out ~/notes/granola --date-col created_at

Default output directory: {DEFAULT_OUT}
Prints per-date note counts and a total; exits non-zero if no date column is found.""",
    )
    p.add_argument("csv_path", help="path to the Granola CSV export to convert")
    p.add_argument("--out", default=DEFAULT_OUT, metavar="DIR",
                   help="root output directory (default: %(default)s)")
    p.add_argument("--date-col", metavar="NAME",
                   help="column used for the date folder (default: first found of "
                        + ", ".join(DATE_CANDIDATES) + ")")
    p.add_argument("--old", metavar="OLD_CSV",
                   help="older CSV export; only rows whose document_id is not in it are imported")
    args = p.parse_args()

    csv.field_size_limit(sys.maxsize)
    old_ids = set()
    if args.old:
        with open(args.old, newline="", encoding="utf-8-sig") as f:
            old_ids = {r["document_id"] for r in csv.DictReader(f) if r.get("document_id")}

    with open(args.csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        date_col = args.date_col or next((c for c in DATE_CANDIDATES if c in fields), None)
        if not date_col:
            sys.exit(f"No date column found; pass --date-col. Columns: {fields}")

        used = set()
        counts = Counter()
        for row in reader:
            if row.get("document_id") in old_ids:
                continue
            date = parse_date(row.get(date_col))
            title = (row.get("document_title") or "").strip()
            folder = os.path.join(args.out, date)
            os.makedirs(folder, exist_ok=True)

            base = safe_name(title)
            name, n = base, 2
            # In incremental mode, don't overwrite notes written by an earlier run.
            while (date, name.lower()) in used or (
                old_ids and os.path.exists(os.path.join(folder, name + ".md"))
            ):
                name = f"{base} ({n})"
                n += 1
            used.add((date, name.lower()))

            content = (
                f"# {title or 'Untitled'}\n\n"
                f"## Notes\n\n{(row.get('notes') or '').strip()}\n\n"
                f"## Summary\n\n{(row.get('summary') or '').strip()}\n\n"
                f"## Transcript\n\n{(row.get('transcript') or '').strip()}\n"
            )
            with open(os.path.join(folder, name + ".md"), "w", encoding="utf-8") as out:
                out.write(content)
            counts[date] += 1

    for date in sorted(counts):
        print(f"{date}: {counts[date]} note(s)")
    print(f"Total: {sum(counts.values())} notes -> {args.out}")


if __name__ == "__main__":
    main()
