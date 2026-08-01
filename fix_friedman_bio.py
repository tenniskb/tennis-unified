#!/usr/bin/env python3
"""Fix corrupted pandoc grid-table patterns in footwork-ready-position.md.

The source file has 'corrupted' grid tables (from .docx -> pandoc -> markdown)
where multiple table cells, images, and captions were jammed into lines separated
by long runs of spaces.

We use a layered approach:
  1. Pattern detection: locate dotted/dashed border lines (`--+` or `=+`).
  2. Inside the block, extract image markdown `![alt](url)` from the merged text.
  3. Clean alt text (strip pandoc auto-generated confidence noise).
  4. Remove the column-boundary padding (mostly 30+ spaces).
  5. Output the image followed by cleaned side-by-side captions or bio text.

Critical: in the broken file, the image markdown may span multiple lines, and
the BIO/CAPTION text may be interleaved at column boundaries. We treat the
problem as: "find every image markdown, strip out the cells, and emit the
leftover text as a caption."
"""
import re
from pathlib import Path

FOOTWORK = Path("docs/01-fundamentals/footwork/footwork-ready-position.md")
DASH_BORDER_MIN_LEN = 30


def parse_dashes_border(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and all(c == "-" for c in stripped) and len(stripped) >= DASH_BORDER_MIN_LEN


COLUMN_SPLIT_MIN_SPACES = 30


def split_columns(line: str):
    """Split a line on a run of 30+ spaces. Returns (col1, col2)."""
    match = re.search(r" {" + str(COLUMN_SPLIT_MIN_SPACES) + r",}", line)
    if match:
        col1 = line[:match.start()].strip()
        col2 = line[match.end():].strip()
        return col1, col2
    return line.strip(), ""


def clean_alt(alt: str) -> str:
    """Strip pandoc auto-generated noise from alt text.

    Common corruptions:
      - "A person playing tennis Description automatically generated with medium"
      - "Description automatically generated with low confidence"
      - bio text leaking in: "medium **Michael Friedman** has been devoted to confidence"
    """
    alt_clean = re.sub(
        r"^[A-Z][^.]*Description automatically generated with\s*",
        "",
        alt,
        flags=re.IGNORECASE,
    ).strip()
    # Bold name (**X**) leaking in means bio text crossed into the alt. Use generic.
    if "**" in alt_clean:
        return "Tennis coach photo"
    alt_clean = re.sub(r"\s+confidence\s*$", "", alt_clean, flags=re.IGNORECASE).strip()
    alt_clean = re.sub(r"(?:^|\s+)(low|medium|high)\s*$", "", alt_clean, flags=re.IGNORECASE).strip()
    alt_clean = re.sub(r"\s+with\s*$", "", alt_clean, flags=re.IGNORECASE).strip()
    alt_clean = re.sub(r"^(with|of|for|in|the)\s+", "", alt_clean, flags=re.IGNORECASE).strip()
    if not alt_clean or len(alt_clean) < 5:
        return "Tennis illustration"
    return alt_clean


def collapse_spaces(text: str) -> str:
    """Collapse runs of spaces and trim."""
    return re.sub(r"\s+", " ", text).strip()


def find_block_end(lines, start_idx):
    """Find the closing border of the grid block starting at start_idx.

    A grid block opens with a border and may contain internal sub-borders.
    The block closes at the LAST border whose NEXT non-empty line is
    text (or EOF), AND which is followed by no further borders within ~10 lines.
    Returns the index AFTER the closing border.
    """
    last_valid = None
    i = start_idx + 1
    while i < len(lines):
        if parse_dashes_border(lines[i]):
            # Look ahead up to 5 lines: count further borders and text lines
            j = i + 1
            text_lines_after = 0
            further_borders = 0
            while j < len(lines) and j < i + 8:
                if parse_dashes_border(lines[j]):
                    further_borders += 1
                    break
                if lines[j].strip():
                    text_lines_after += 1
                j += 1
            # This is a closing border if it has text immediately after (with maybe empty lines)
            # AND no further borders within a few lines (the next border is the close)
            if further_borders == 0 and j < len(lines) and text_lines_after > 0:
                # Next border isn't a sub-border; this is the closing border
                # But we need to return AFTER the NEXT border if there is one
                # Actually — if text_lines_after > 0 and next non-empty is text, this is closing
                last_valid = i + 1
            elif further_borders > 0:
                # There's another border soon — this might be a sub-border; keep scanning
                pass
            else:
                # No text, no further borders within range; if this is the last border, it's closing
                last_valid = i + 1
        i += 1
    return last_valid if last_valid is not None else len(lines)


def extract_image_from_block(lines, start_idx, end_idx):
    """Extract image markdown from the block [start_idx, end_idx).

    Returns (image_md, replacement_text) where replacement_text is text
    that should remain in the output besides the image (i.e., captions/bio).

    Key insight: the image lives in column 1; bio/caption lives in column 2.
    We process each line by splitting on 30+ spaces, joining only col1 to
    find the image, and joining col2 separately for the bio.
    """
    col1_lines = []
    col2_lines = []
    for k in range(start_idx + 1, end_idx):
        col1, col2 = split_columns(lines[k])
        col1_lines.append(col1)
        col2_lines.append(col2)
    col1_text = "\n".join(col1_lines)
    # Find image in col1 only — this avoids capturing bio text in col2
    m = re.search(r"!\[([^\]]*)\]\(([^)]+)\)", col1_text, re.DOTALL)
    if not m:
        return None, None
    alt_raw = m.group(1)
    url = m.group(2).strip()
    alt = clean_alt(collapse_spaces(alt_raw))
    image_md = f"![{alt}]({url})"

    # Now collect col2 (bio/caption) lines, stripping any all-dashes borders
    # and stripping phantom image alts (without closing URL).
    bio_pieces = []
    for cl in col2_lines:
        stripped = cl.strip()
        if not stripped:
            continue
        # Skip border-only lines
        if all(c == "-" for c in stripped) and len(stripped) >= DASH_BORDER_MIN_LEN:
            continue
        # Skip phantom image alts (no closing `](` pair)
        if stripped.startswith("![") and "]" not in stripped:
            continue
        # Skip other stray `![` fragments
        if stripped.startswith("![") and "](" not in stripped:
            continue
        bio_pieces.append(stripped)
    bio_text = " ".join(bio_pieces)
    bio_text = re.sub(r"\s+", " ", bio_text).strip()
    return image_md, bio_text


def detect_and_fix(lines, i):
    """If lines[i] opens a corrupted grid block, emit replacement. Else None.

    Returns (replacement_str, lines_consumed) or None.
    """
    if not parse_dashes_border(lines[i]):
        return None

    # Look at the next ~6 lines to see if this is our pattern
    end_idx = find_block_end(lines, i)
    if end_idx - i < 2:
        return None

    # Quick check: does the block contain an image markdown?
    block_text = "\n".join(lines[i + 1:end_idx])
    if "![" not in block_text or "](media_" not in block_text:
        return None

    image_md, caption = extract_image_from_block(lines, i, end_idx)
    if not image_md:
        return None

    if caption:
        # Ensure bolded caption
        if not caption.startswith("**"):
            caption = f"**{caption}**"
        return f"{image_md}\n\n{caption}", end_idx
    return image_md, end_idx


def fix_file(path: Path) -> bool:
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()
    new_lines = []
    i = 0
    fixed_count = 0

    while i < len(lines):
        if parse_dashes_border(lines[i]):
            result = detect_and_fix(lines, i)
            if result is not None:
                block, consumed = result
                new_lines.append(block)
                i = consumed
                fixed_count += 1
                continue
        new_lines.append(lines[i])
        i += 1

    new_content = "\n".join(new_lines) + "\n"
    if new_content != content:
        path.write_text(new_content, encoding="utf-8")
        print(f"  Fixed {fixed_count} blocks in: {path}")
        return True
    print(f"  No change: {path}")
    return False


def main():
    if not FOOTWORK.exists():
        print(f"ERROR: {FOOTWORK} not found")
        return 1
    print(f"Processing: {FOOTWORK}")
    fix_file(FOOTWORK)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
