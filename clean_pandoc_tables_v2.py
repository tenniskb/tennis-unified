"""Comprehensive pandoc artifact cleaner for tennisplayer.net content.

Handles two issues:
1. Pandoc pipe-tables with `+----+`, `+====+` borders → real markdown tables
   (or grid layouts for image+caption rows).
2. Escaped apostrophes (`\'`) → real apostrophes (`'`).

Also fixes:
- Strip `{width=...}` / `{height=...}` from image references.
- Replace standalone `\\---` lines with `<hr>` only if not a table separator.
"""
from __future__ import annotations

import re
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent
TARGET_DIRS = ["01-fundamentals", "02-more", "03-stroke-analysis", "04-new-issue",
               "05-foundation", "06-advanced", "07-elite"]

# Escape pattern: literal backslash + apostrophe
ESCAPED_QUOTE_RE = re.compile(r"\\'")

# Width/height attrs on images
WIDTH_ATTR_LOOSE = re.compile(r"\{(?:width|height)=[^{}]*\}", re.DOTALL)

# Pandoc pipe-table separator: +----+----+ or +:===:+:===:+
# Match any sequence of [+][-:==]+  with 2+ cells (at least 2 + signs in a row pattern)
TABLE_SEP_RE = re.compile(r"^\s*\+(?:[-:=]+\+){2,}\s*\r?$")
# Pipe-table row (starts/ends with | but may have multiple pipes)
PIPE_ROW_RE = re.compile(r"^\s*\|.*\|")


def clean_apostrophes(text: str) -> str:
    """Convert `\\'`, `[\\'`, `\\']` ... to apostrophes."""
    return ESCAPED_QUOTE_RE.sub("'", text)


def clean_width_attrs(text: str) -> str:
    """Remove {width=...} / {height=...} attrs from image refs."""
    prev = None
    while prev != text:
        prev = text
        text = WIDTH_ATTR_LOOSE.sub("", text)
    return text


def parse_pandoc_table(lines: list[str], start: int) -> tuple[list[list[str]], int]:
    """Parse a pandoc pipe-table starting at index `start`.

    Returns (rows, next_index) where rows is a list of [cell1, cell2, ...]
    and next_index is the line after the table block.

    Supports:
      +---+---+
      | a | b |   <- row 1
      +===+===+
      | c | d |   <- row 2
      +---+---+
    """
    rows: list[list[str]] = []
    i = start
    while i < len(lines):
        line = lines[i]
        if PIPE_ROW_RE.match(line):
            # Split row into cells, strip leading/trailing pipe, then split
            # on every `|` that has an even count of backslashes before it (simplified)
            content = line.strip()
            if content.startswith("|"):
                content = content[1:]
            if content.endswith("|"):
                content = content[:-1]
            # Split on unescaped `|` - but pandoc cells don't escape pipes, so simple split
            cells = [c.strip() for c in content.split("|")]
            rows.append(cells)
        elif TABLE_SEP_RE.match(line):
            # Separator line - skip
            pass
        else:
            break
        i += 1
    return rows, i


def is_multiline_text(cell: str) -> bool:
    """True if cell contains multiple paragraphs (numbered list or breaks)."""
    return "\n" in cell or "\n\n" in cell


def emit_clean_table(rows: list[list[str]]) -> str:
    """Convert parsed rows into a clean markdown table.

    For single-row single-column tables, just emit the cell content.
    For multi-column tables, emit a proper markdown table.
    """
    if not rows:
        return ""
    # Normalize number of columns to max
    max_cols = max(len(r) for r in rows)
    norm_rows = [r + [""] * (max_cols - len(r)) for r in rows]
    # If only one row, just emit the content
    if len(norm_rows) == 1:
        return "\n\n".join(c for c in norm_rows[0] if c.strip()) + "\n\n"
    # Otherwise emit a markdown table
    out = ["| " + " | ".join(norm_rows[0]) + " |"]
    out.append("| " + " | ".join(["---"] * max_cols) + " |")
    for r in norm_rows[1:]:
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out) + "\n\n"


def transform_pandoc_tables(text: str) -> str:
    """Replace pandoc pipe-tables with clean markdown tables."""
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if TABLE_SEP_RE.match(line):
            # Find the table block - look back for continuous pipe rows
            j = len(out) - 1
            while j >= 0 and PIPE_ROW_RE.match(out[j]):
                j -= 1
            table_start = j + 1
            # Only treat as table if previous lines are pipe rows
            if table_start == len(out):
                # Table starts at the beginning of output
                # Look back at original lines (i-1) for pipe rows
                back = i - 1
                # We can include the separator itself as standalone
                # but it needs pipe rows before it; otherwise skip
                i += 1
                continue
            prev_rows_lines = out[table_start:]
            # Look forward for more pipe rows / separators
            k = i + 1
            while k < len(lines) and (PIPE_ROW_RE.match(lines[k]) or TABLE_SEP_RE.match(lines[k])):
                k += 1
            # Collect all rows
            all_block_lines = prev_rows_lines + [line] + lines[i + 1 : k]
            parsed_rows, _ = parse_pandoc_table(all_block_lines, 0)
            # Remove the previous pipe rows from output
            del out[table_start:]
            out.append(emit_clean_table(parsed_rows))
            i = k
        else:
            out.append(line)
            i += 1
    return "\n".join(out)


def clean_file(path: pathlib.Path) -> tuple[bool, str]:
    """Clean a single markdown file. Returns (changed, summary)."""
    original = path.read_text(encoding="utf-8", errors="ignore")
    text = original
    changes = []
    # 1. Apostrophes
    new_text = clean_apostrophes(text)
    if new_text != text:
        n = text.count("\\'")
        changes.append(f"apostrophes={n}")
        text = new_text
    # 2. Width attrs
    new_text = clean_width_attrs(text)
    if new_text != text:
        n = len(WIDTH_ATTR_LOOSE.findall(text))
        changes.append(f"width_attrs={n}")
        text = new_text
    # 3. Pandoc tables
    new_text = transform_pandoc_tables(text)
    if new_text != text:
        n = sum(1 for ln in text.split("\n") if TABLE_SEP_RE.match(ln))
        changes.append(f"tables={n}")
        text = new_text
    if text != original:
        path.write_text(text, encoding="utf-8")
    return bool(changes), ", ".join(changes) if changes else "no change"


def main():
    targets = []
    for td in TARGET_DIRS:
        d = REPO / "docs" / td
        if d.exists():
            targets.extend(d.rglob("*.md"))
    print(f"Processing {len(targets)} files...")
    total_changed = 0
    for p in targets:
        changed, summary = clean_file(p)
        if changed:
            total_changed += 1
            # Only print files that changed
            print(f"  {p.relative_to(REPO)}: {summary}")
    print(f"\nDone. {total_changed}/{len(targets)} files changed.")


if __name__ == "__main__":
    main()