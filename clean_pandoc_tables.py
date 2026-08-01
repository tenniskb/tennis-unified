"""Clean up pandoc-emitted artifacts across tennisplayer.net content:

1. Remove inline `{width="..." height="..."}` from image refs.
2. Convert pandoc pipe-tables that wrap an image+caption layout into clean
   side-by-side flow (image first, then the caption paragraph).
3. Strip the standalone horizontal-rule divider lines (`----...----`).

Approach: regex-driven, line-by-line rewrite that preserves all narrative
text and image references but un-breaks the layout.
"""
from __future__ import annotations

import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parent
# Only target the tennisplayer.net-derived folders; tenniskb/coauthored
# content is hand-curated and should stay as-is.
TARGET_DIRS = ["01-fundamentals", "02-more", "03-stroke-analysis", "04-new-issue"]

WIDTH_ATTR = re.compile(r"\{width=\"[^\"]*\"\s*height=\"[^\"]*\"\s*\}|"
                        r"\{width=\"[^\"]*\"\s*\}|"
                        r"\{height=\"[^\"]*\"\s*\}", re.DOTALL)
WIDTH_ATTR_LOOSE = re.compile(r"\{(?:width|height)=[^{}]*\}", re.DOTALL)

# Match a pipe-table row that contains only an image ref (with optional caption text)
IMG_CELL_RE = re.compile(r"^\s*\|\s*!\[.*?\]\([^)]+\)\s*(?:\{[^{}]*\})?\s*\|\s*$")
# Match any row in a pipe-table
TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")
# Match table separator (+----+----+ or +:===:+:===:+)
TABLE_SEP_RE = re.compile(r"^\s*\+[:=-]+(\+[:=-]+)+\s*$")
# Match image row in a table cell followed by other cells of caption text
TABLE_BLOCK_RE = re.compile(
    r"(\n|^)"
    r"(?P<table>(?:^[ \t]*\|.*\|\s*\n)+)"  # one or more pipe rows
    r"(?:^[ \t]*\+[:=-]+(\+[:=-]+)+\s*\n)?"  # optional separator
)


def clean_width_attrs(text: str) -> str:
    """Remove pandoc width/height attribute blocks from image references."""
    # Repeat to catch nested cases (rare)
    prev = None
    while prev != text:
        prev = text
        text = WIDTH_ATTR_LOOSE.sub("", text)
    return text


def unbreak_pandoc_table(text: str) -> str:
    """Convert pandoc-emitted pipe-tables back to clean flowing markdown.

    pandoc emits tables like:
        +-------+-------+
        | img   | text  |
        +=======+=======+
        | text  | text  |
        +-------+-------+

    We detect any line that is a table separator and convert the block of
    pipe-rows surrounding it into a sequence of paragraphs, splitting
    pipe-cells with blank lines so each cell becomes its own block.
    """
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if TABLE_SEP_RE.match(line):
            # Look backward for the start of the table block (consecutive pipe rows)
            j = len(out) - 1
            while j >= 0 and TABLE_ROW_RE.match(out[j]):
                j -= 1
            table_start = j + 1
            # Look forward for the end of the table block
            k = i + 1
            while k < len(lines) and (TABLE_ROW_RE.match(lines[k]) or TABLE_SEP_RE.match(lines[k])):
                k += 1
            # table_start..i-1 are pipe rows, i is separator, i+1..k-1 are next rows / separators
            # Collect all pipe rows in the whole block
            block_rows = out[table_start:]
            block_rows.append(line)
            block_rows.extend(lines[i + 1 : k])
            # Group rows by "visual row" — separated by separator lines
            rows: list[list[str]] = []
            cur: list[str] = []
            for r in block_rows:
                if TABLE_SEP_RE.match(r):
                    if cur:
                        rows.append(cur)
                        cur = []
                else:
                    cur.append(r)
            if cur:
                rows.append(cur)

            # Replace out[table_start:] with cell-by-cell paragraphs
            del out[table_start:]
            for r_idx, row in enumerate(rows):
                # Split each row into cells
                cells: list[str] = []
                for row_line in row:
                    parts = [c.strip() for c in row_line.strip().strip("|").split("|")]
                    cells.extend(parts)
                # Strip empty cells
                cells = [c for c in cells if c]
                if not cells:
                    continue
                # First cell is the image (typical pandoc layout); rest are caption text
                # Join them with blank line between to render side-by-side as block flow
                if len(cells) == 1:
                    out.append(cells[0])
                else:
                    # Put image first, then text cells
                    img_cell = cells[0]
                    text_cells = cells[1:]
                    out.append(img_cell)
                    out.append("")
                    for tc in text_cells:
                        out.append(tc)
                        out.append("")
                if r_idx < len(rows) - 1:
                    out.append("")
            i = k
            continue
        out.append(line)
        i += 1
    return "\n".join(out)


def strip_divider_lines(text: str) -> str:
    """Remove pandoc-emitted '---...---' divider lines that wrap standalone images."""
    lines = text.split("\n")
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        # A divider that wraps a single block: just dashes (>= 10)
        if re.match(r"^-{10,}$", stripped):
            continue
        out.append(line)
    return "\n".join(out)


def clean_file(md: pathlib.Path) -> int:
    try:
        original = md.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return 0
    text = original
    text = unbreak_pandoc_table(text)
    text = strip_divider_lines(text)
    text = clean_width_attrs(text)
    if text != original:
        md.write_text(text, encoding="utf-8")
        return 1
    return 0


def main() -> None:
    DOCS = REPO / "docs"
    total_files = 0
    changed = 0
    for sub in TARGET_DIRS:
        target = DOCS / sub
        if not target.is_dir():
            print(f"Skip: {target} not found")
            continue
        for md in target.rglob("*.md"):
            total_files += 1
            if clean_file(md):
                changed += 1
    print(f"Files scanned: {total_files}")
    print(f"Files cleaned: {changed}")


if __name__ == "__main__":
    main()
