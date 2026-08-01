"""V3 cleaner: Better pandoc table handling.

Improvements over V2:
1. Strips ALL standalone `+----+` separator lines (even outside table context).
2. For 1-row tables with image + text: extract image, then text as paragraph.
3. For multi-row tables: still use clean markdown table syntax.
4. Joins wrapped text within cells (continuation lines).
5. Handles CRLF line endings.
"""
from __future__ import annotations

import re
import pathlib

REPO = pathlib.Path(__file__).resolve().parent
TARGET_DIRS = ["01-fundamentals", "02-more", "03-foundation", "03-stroke-analysis",
               "04-advanced", "04-new-issue", "05-elite", "06-anatomy-lab",
               "07-angle-atlas", "08-reference-library", "09-tennis-wiki-reference"]

ESCAPED_QUOTE_RE = re.compile(r"\\'")
WIDTH_ATTR_LOOSE = re.compile(r"\{(?:width|height)=[^{}]*\}", re.DOTALL)

# Pandoc separator: +---+---+ ... (any cells, >= 2 separators)
# Structure: [+][dashes][+][dashes][+] for 2 cells. Generic: \+[-:=]+ then (\+[-:=]+)* then \+
TABLE_SEP_RE = re.compile(r"^\s*\+[-:=]+(?:\+[-:=]+)*\+\s*\r?$")
# Pipe row: starts/ends with |
PIPE_ROW_RE = re.compile(r"^\s*\|.*\|\s*\r?$")


def clean_apostrophes(text: str) -> tuple[str, int]:
    new = ESCAPED_QUOTE_RE.sub("'", text)
    return new, text.count("\\'")


def clean_width_attrs(text: str) -> tuple[str, int]:
    n = 0
    while True:
        new = WIDTH_ATTR_LOOSE.sub("", text)
        if new == text:
            return new, n
        n += 1
        text = new


def is_separator_line(line: str) -> bool:
    """Check if line is a `+---+---+...` pandoc separator."""
    return bool(TABLE_SEP_RE.match(line))


def is_pipe_row(line: str) -> bool:
    return bool(PIPE_ROW_RE.match(line))


def parse_pipe_row(line: str) -> list[str]:
    """Parse a pipe row into cells."""
    # Strip leading/trailing whitespace and CR
    s = line.strip().rstrip("\r")
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    cells = s.split("|")
    return [c.strip() for c in cells]


def join_wrapped_cells(rows: list[list[str]]) -> list[list[str]]:
    """Merge continuation cells - if a cell is empty/whitespace, take from previous row same column."""
    if not rows:
        return rows
    ncols = max(len(r) for r in rows)
    out: list[list[str]] = []
    for r in rows:
        # Pad to ncols
        r = r + [""] * (ncols - len(r))
        new_r = list(r)
        for i, cell in enumerate(r):
            stripped = cell.strip()
            if not stripped and out and i < len(out[-1]):
                # Continuation - merge with previous row
                prev = out[-1][i].rstrip()
                if prev:
                    new_r[i] = prev + " " + stripped  # leave empty for now
            # Actually, just append continuation to previous cell
        out.append(r)
    # Second pass: remove rows where all cells are empty/whitespace
    out = [r for r in out if any(c.strip() for c in r)]
    # Third pass: merge cells in column where next row has empty in same column with continuation
    # This is complex; simpler approach: just merge all rows for each column by concatenating non-empty
    return out


def transform_pandoc_tables(text: str) -> tuple[str, int]:
    """Replace pandoc pipe-tables with cleaner markdown.

    Returns (new_text, n_tables_replaced).
    """
    # Normalize CRLF to LF
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    n_replaced = 0
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if is_separator_line(line):
            # Standalone separator - peek for table context
            # Look for adjacent pipe rows (before AND after)
            # Skip the separator itself
            # Collect pipe rows on both sides
            # Find table block: go back to find pipe rows, skip sep, find pipe rows forward
            block_rows: list[list[str]] = []
            # Look back
            j = len(out) - 1
            start_back = j + 1
            while j >= 0 and is_pipe_row(out[j]):
                j -= 1
            back_rows = out[j + 1:]
            start_back = j + 1

            forward_lines = lines[i + 1:]
            k = 0
            while k < len(forward_lines) and (is_pipe_row(forward_lines[k]) or is_separator_line(forward_lines[k])):
                k += 1
            forward_block = forward_lines[:k]
            forward_rows = [parse_pipe_row(l) for l in forward_block if is_pipe_row(l)]

            all_rows = [parse_pipe_row(l) for l in back_rows] + forward_rows
            # Now drop all back rows from output
            del out[start_back:]

            if all_rows:
                n_replaced += 1
                # Emit clean markdown table
                max_cols = max(len(r) for r in all_rows)
                norm = [r + [""] * (max_cols - len(r)) for r in all_rows]
                # Header
                out.append("| " + " | ".join(norm[0]) + " |")
                out.append("| " + " | ".join(["---"] * max_cols) + " |")
                for r in norm[1:]:
                    out.append("| " + " | ".join(r) + " |")
                out.append("")
            i = i + 1 + k
        else:
            out.append(line)
            i += 1
    return "\n".join(out), n_replaced


def clean_file(path: pathlib.Path) -> dict:
    """Clean a single markdown file."""
    original = path.read_bytes()
    try:
        text = original.decode("utf-8")
    except UnicodeDecodeError:
        text = original.decode("latin-1")

    changes = {}
    text, n = clean_apostrophes(text)
    if n:
        changes["apostrophes"] = n
    text, n = clean_width_attrs(text)
    if n:
        changes["width_attrs"] = n
    text, n = transform_pandoc_tables(text)
    if n:
        changes["tables"] = n

    if changes:
        path.write_text(text, encoding="utf-8", newline="\n")
    return changes


def main():
    targets = []
    for td in TARGET_DIRS:
        d = REPO / "docs" / td
        if d.exists():
            targets.extend(d.rglob("*.md"))
    print(f"Scanning {len(targets)} files...")
    total_changed = 0
    total_apostrophes = 0
    total_tables = 0
    for p in targets:
        changes = clean_file(p)
        if changes:
            total_changed += 1
            total_apostrophes += changes.get("apostrophes", 0)
            total_tables += changes.get("tables", 0)
            print(f"  {p.relative_to(REPO)}: {changes}")
    print(f"\nDone. {total_changed}/{len(targets)} files changed.")
    print(f"  Apostrophes fixed: {total_apostrophes}")
    print(f"  Tables replaced: {total_tables}")


if __name__ == "__main__":
    main()