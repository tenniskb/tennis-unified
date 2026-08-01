"""Debug friedman bio detection - more lines."""
import re

DASH_BORDER_RE = re.compile(r"^[ \t]*-{20,}\s*$")
IMAGE_LINE_RE = re.compile(
    r"^[ \t]*(!\[[^\]]*\]\([^)]+\))(\s{30,})(.*)$",
    re.DOTALL
)

with open(r"C:\Users\Henry\Documents\GitHub\tennis-unified\docs\01-fundamentals\footwork\footwork-ready-position.md", "rb") as f:
    raw = f.read()

text = raw.decode('utf-8').replace('\r\n', '\n')
lines = text.split('\n')

# Show lines 244-260
for i in range(244, min(265, len(lines))):
    line = lines[i]
    has_img = 'image10' in line or 'jpeg' in line
    has_friedman = 'Friedman' in line
    print(f"L{i} (len={len(line)}): {'[IMG]' if has_img else ''}{'[FRIED]' if has_friedman else ''} {line[:120]!r}")

# Check line 245 specifically
line_245 = lines[245]
print(f"\nL245 full repr: {line_245!r}")
print(f"  Length: {len(line_245)}")
m = IMAGE_LINE_RE.match(line_245)
print(f"  Match: {m is not None}")

# Find any line with ![ pattern
for i, line in enumerate(lines):
    if line.lstrip().startswith('!['):
        print(f"\nFound ![ at line {i}: {line[:200]!r}")
        break