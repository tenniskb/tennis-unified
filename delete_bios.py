#!/usr/bin/env python3
"""Delete author bio blocks from the end of tennis articles.

Heuristics for detecting a bio block at end of file:
  - Located in the last 30% of the file
  - Often preceded by a horizontal rule (---) or a final article image
  - Author name in plain text (first letters capitalized, multiple words)
  - Mentions personal credentials (former Pro Circuit, has coached, etc.)
  - Often contains external URLs (podcast, blog, camp, online academy)
  - Mentions books, programs, or academies by name

The script is conservative — it only deletes paragraphs that match MANY
of these patterns simultaneously. If a bio block is detected, the
script also removes the image immediately before it (since bios
typically have an author photo).
"""
import re
from pathlib import Path

# Regex patterns that suggest a bio paragraph
BIO_PATTERNS = [
    r"former\s+#?\d+\s+for\s+\w+",   # "former #1 for Cornell"
    r"Pro\s+Circuit\s+player",
    r"has\s+coached\s+(numerous|many|top|juniors)",
    r"is\s+a\s+leading\s+coach",
    r"has\s+written\s+(\w+\s+)?best-selling",
    r"runs\s+a\s+popular",
    r"tennis\s+camp",
    r"virtual\s+school",
    r"online\s+academy",
    r"weekly\s+(high\s+performance\s+)?tennis\s+video",
    r"podcast",
    r"all\s+(other\s+)?podcasting\s+directories",
    r"Check\s+out\s+\w+'s\s+blog",
    r"Learn\s+about\s+(his|her)",
    r"Visit\s+\w+\.com",
    r"high\s+performance\s+(summer\s+)?(tennis\s+)?camp",
    r"best-selling\s+book",
    r"has\s+authored\s+(\w+\s+)?book",
    r"Pro\s+of\s+the\s+Year",
    r"USPTA\s+\w+",
    r"USTA\s+\w+",
    r"named\s+\w+\s+of\s+the\s+Year",
    r"acclaimed\s+(author|coach)",
    r"ProdigyMaker",
    r"Tennis\s+Technique\s+Bible",
    r"Secrets\s+of\s+Spanish\s+Tennis",
    r"formerly\s+(a|an)\s+professional",
    r"professional\s+tennis\s+(player|career)",
    r"has\s+been\s+(a|devoted\s+to\s+tennis)",
    r"Tennis\s+Director",
    r"Millennium\s+Sports\s+Club",
    r"Rancho\s+Solano",
]

BIO_PATTERN_RE = re.compile("|".join(BIO_PATTERNS), re.IGNORECASE)


def looks_like_bio(text: str) -> bool:
    """Return True if a paragraph matches many bio patterns."""
    matches = len(BIO_PATTERN_RE.findall(text))
    return matches >= 2


def find_bio_start(lines: list) -> int:
    """Find the line index where the bio block starts at the end of file.

    Returns the line index of the first bio paragraph, or -1 if no bio found.
    Only looks at the last 40% of the file.
    """
    search_start = int(len(lines) * 0.60)
    # Walk backwards from end, find the start of the bio block
    # Bio blocks typically start with a paragraph that has author's full name + credentials
    # Walk from end backwards, accumulating consecutive bio paragraphs
    bio_start = -1
    consecutive_bio_paragraphs = 0
    for i in range(len(lines) - 1, search_start - 1, -1):
        line = lines[i].strip()
        if not line:
            # Empty line — boundary
            if consecutive_bio_paragraphs >= 1:
                bio_start = i + 1
                break
            continue
        if looks_like_bio(line):
            consecutive_bio_paragraphs += 1
        else:
            # Non-bio content
            if consecutive_bio_paragraphs >= 1:
                # Bio block ends here
                bio_start = i + 1
                break
            consecutive_bio_paragraphs = 0
    return bio_start


def delete_bio_from_file(path: Path) -> bool:
    """Delete the bio block at end of file. Returns True if changed."""
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()
    bio_start = find_bio_start(lines)
    if bio_start < 0:
        return False
    # Also delete any horizontal rule or image line just before the bio
    i = bio_start - 1
    while i >= 0:
        line = lines[i].strip()
        if not line:
            i -= 1
            continue
        if line.startswith("![") or line.startswith("---") or line == "***" or line.startswith("___"):
            bio_start = i
            i -= 1
        else:
            break
    # Remove the bio block
    new_lines = lines[:bio_start]
    # Trim trailing empty lines but keep at most 2 (to preserve article end formatting)
    while len(new_lines) > 1 and not new_lines[-1].strip() and not new_lines[-2].strip():
        new_lines.pop()
    if new_lines and not new_lines[-1].strip():
        new_lines.pop()
    new_content = "\n".join(new_lines) + "\n"
    if new_content != content:
        path.write_text(new_content, encoding="utf-8")
        return True
    return False


def main():
    docs_root = Path("docs")
    changed_files = []
    for path in docs_root.rglob("*.md"):
        if delete_bio_from_file(path):
            changed_files.append(path)
    print(f"\nDeleted bio blocks from {len(changed_files)} files:")
    for f in changed_files:
        print(f"  {f}")


if __name__ == "__main__":
    main()