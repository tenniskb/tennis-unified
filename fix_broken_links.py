"""Rewrite broken .md links in OLD stub index.md files to point at real articles in numbered folders."""
import re
import pathlib

DOCS = pathlib.Path('docs')

# Build basename index across all docs/
all_basenames = {}
for f in DOCS.rglob('*.md'):
    all_basenames.setdefault(f.stem, []).append(f)


def normalize_stem(s):
    """Aggressive normalization for fuzzy matching: lowercase, strip separators, strip trailing 's'."""
    s = s.lower().replace('-', '').replace('_', '').replace("'", '')
    if s.endswith('s'):
        s = s[:-1]
    return s


# Build normalized basename index
all_normalized = {}
for stem, paths in all_basenames.items():
    n = normalize_stem(stem)
    all_normalized.setdefault(n, []).extend(paths)

# Numbered folder prefixes
NUMBERED_PREFIXES = ('01-fundamentals', '02-', '03-stroke-analysis', '04-',
                     '05-', '06-', '07-', '08-')


def find_best_match(stem):
    """Find best match for a stem. Try exact first, then normalized."""
    if stem in all_basenames:
        cands = all_basenames[stem]
    else:
        n = normalize_stem(stem)
        if n in all_normalized:
            cands = all_normalized[n]
        else:
            return None
    numbered = [c for c in cands
                if any(p in str(c) for p in NUMBERED_PREFIXES)]
    return numbered[0] if numbered else cands[0]


def rewrite_links(text, source_file):
    """Rewrite broken .md links to point at real articles."""
    def fix_link(m):
        link_text = m.group(1)
        link_path = m.group(2)
        anchor = m.group(3) or ''
        if link_path.startswith('/') or link_path.startswith('http'):
            return m.group(0)
        target = (source_file.parent / link_path).resolve()
        if target.exists():
            return m.group(0)  # Already valid
        stem = pathlib.Path(link_path).stem
        chosen = find_best_match(stem)
        if chosen is None:
            return m.group(0)  # No match - leave for manual fix
        rel_parts = chosen.relative_to(DOCS).parts
        src_parts = source_file.parent.relative_to(DOCS).parts
        ups = len(src_parts)
        ups_path = '../' * ups
        down_path = '/'.join(rel_parts)
        rel = ups_path + down_path
        return f'[{link_text}]({rel}{anchor})'
    return re.sub(r'\[([^\]]*)\]\(([^)]+\.md)(#[^)]*)?\)', fix_link, text)


# Files to process (QA gate: do ONE first, then the rest after user QA)
TARGETS = [
    'docs/stroke-analysis/biomechanics/index.md',
    'docs/stroke-analysis/tour-strokes/index.md',
    'docs/stroke-analysis/advanced-tennis/index.md',
]

for t in TARGETS:
    p = pathlib.Path(t)
    if not p.exists():
        print(f'NOT FOUND: {t}')
        continue
    text = p.read_text(encoding='utf-8', errors='ignore')
    new_text = rewrite_links(text, p)
    if new_text != text:
        p.write_text(new_text, encoding='utf-8')
        diff_count = sum(1 for a, b in zip(text.split('\n'), new_text.split('\n')) if a != b)
        print(f'UPDATED: {t} ({diff_count} line(s) changed)')
    else:
        print(f'NO CHANGE: {t}')