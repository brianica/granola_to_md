# Granola CSV → Markdown

`csv_to_md.py` converts a Granola CSV export into Markdown notes, one folder per date and one file per meeting.

Requires Python 3 (standard library only).

## Usage

```bash
# Full import: every row, overwriting existing notes
python3 csv_to_md.py export.csv

# Incremental: only rows not present in an older export
python3 csv_to_md.py new_export.csv --old previous_export.csv

# Custom output directory / date column
python3 csv_to_md.py export.csv --out ~/notes/granola --date-col created_at
```

To set a default output directory, add this to `~/.zshrc`:

```bash
export GRANOLA_NOTES_DIR="$HOME/Google Drive/My Drive/_notes/granola"
```

Run `python3 csv_to_md.py --help` for the full reference.

| Option | Description |
|---|---|
| `csv_path` | Granola CSV export to convert |
| `--out DIR` | Output root (default: `$GRANOLA_NOTES_DIR`, else `./granola_notes`) |
| `--date-col NAME` | Column for the date folder (default: first found of `document_created`, `date`, `created_at`, `meeting_date`, `start_time`, `updated_at`) |
| `--old OLD_CSV` | Older export; rows whose `document_id` appears in it are skipped |

## Input

Expected columns: `document_id`, `document_title`, `document_created`, `notes`, `summary`, `transcript`. Other columns (e.g. `user_email`, `workspace_name`) are ignored.

## Output

```
<out>/
  2026-10-01/
    Weekly Sync.md
    Weekly Sync (2).md
  2026-10-02/
    Design Review.md
```

Each file contains:

```markdown
# <document_title>

## Notes
...

## Summary
...

## Transcript
...
```

- Filename characters invalid on macOS/Windows (`/ \ : * ? " < > |`) become spaces; names are capped at 150 characters; an empty title becomes `Untitled`.
- Duplicate titles on the same date get ` (2)`, ` (3)`, ….
- Dates are parsed as ISO 8601 and formatted `YYYY-MM-DD`; unparseable values use their first 10 characters; empty values go to `undated/`.

## Modes

- **Full import** (no `--old`): writes every row and overwrites existing files, so reruns are idempotent.
- **Incremental** (`--old`): writes only new rows and never overwrites an existing file (a name clash gets a ` (n)` suffix). Edits to meetings already in the old CSV are **not** applied — run a full import to refresh them.

The script prints the number of notes written per date and a total, and exits non-zero if no date column is found.
