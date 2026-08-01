import os, sys, pathlib, re, subprocess, shutil

sys.stdout.reconfigure(encoding='utf-8')

repo = pathlib.Path(r'C:/Users/Henry/Documents/GitHub/tennis-unified')
docs = repo / 'docs'

tfl_src = pathlib.Path(r'C:/Users/Henry/Documents/New Tennis Knowledge/TFL Manuals')
books_src = pathlib.Path(r'C:/Users/Henry/Documents/New Tennis Knowledge/Tennis Books')

tfl_dest = docs / '08-reference-library' / 'tfl-manuals'
books_dest = docs / '08-reference-library' / 'tennis-books'

tfl_dest.mkdir(parents=True, exist_ok=True)
books_dest.mkdir(parents=True, exist_ok=True)

def slugify(title):
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', title).strip('-').lower()
    return slug if slug else 'doc'

print("Processing TFL Manuals...")
tfl_articles = []
for p in sorted(tfl_src.glob('*')):
    if p.name.startswith('~$'):
        continue
    stem = p.stem
    slug = slugify(stem)
    
    if p.suffix == '.docx':
        md_file = tfl_dest / f"{slug}.md"
        media_dir = tfl_dest / f"media_{slug}"
        cmd = ['pandoc', str(p), '-o', str(md_file), '--extract-media', str(media_dir)]
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            txt = md_file.read_text(encoding='utf-8', errors='ignore')
            target_dir_str = str(tfl_dest).replace('\\', '/')
            txt_clean = txt.replace(target_dir_str + '/', '')
            txt_clean = txt_clean.replace(str(tfl_dest) + '\\', '')
            if not txt_clean.startswith('# '):
                txt_clean = f"# {stem}\n\n" + txt_clean
            md_file.write_text(txt_clean, encoding='utf-8')
            tfl_articles.append((stem, f"{slug}.md"))
            print(f"  Converted docx: {stem}")
        except Exception as e:
            print(f"  Error converting {p.name}: {e}")

    elif p.suffix in ['.md', '.html', '.txt']:
        md_file = tfl_dest / f"{slug}.md"
        try:
            txt = p.read_text(encoding='utf-8', errors='ignore')
            if not txt.startswith('# '):
                txt = f"# {stem}\n\n" + txt
            md_file.write_text(txt, encoding='utf-8')
            tfl_articles.append((stem, f"{slug}.md"))
            print(f"  Copied text: {stem}")
        except Exception as e:
            print(f"  Error reading {p.name}: {e}")

# Index for TFL Manuals
tfl_links = "\n".join([f"- [{title}]({filename})" for title, filename in sorted(tfl_articles, key=lambda x: x[0])])
tfl_index = f"""---
title: TFL Training Manuals
description: Official Tennis Future Lab (TFL) training manuals, scaffolds, and biomechanics guides.
---

# TFL Training Manuals

Total Manuals: {len(tfl_articles)}

---

## Manuals Index

{tfl_links}
"""
(tfl_dest / 'index.md').write_text(tfl_index, encoding='utf-8')

print("\nProcessing Tennis Books...")
books_articles = []
for p in sorted(books_src.glob('*')):
    if p.name.startswith('~$'):
        continue
    stem = p.stem
    slug = slugify(stem)
    
    if p.suffix == '.docx':
        md_file = books_dest / f"{slug}.md"
        media_dir = books_dest / f"media_{slug}"
        cmd = ['pandoc', str(p), '-o', str(md_file), '--extract-media', str(media_dir)]
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            txt = md_file.read_text(encoding='utf-8', errors='ignore')
            target_dir_str = str(books_dest).replace('\\', '/')
            txt_clean = txt.replace(target_dir_str + '/', '')
            txt_clean = txt_clean.replace(str(books_dest) + '\\', '')
            if not txt_clean.startswith('# '):
                txt_clean = f"# {stem}\n\n" + txt_clean
            md_file.write_text(txt_clean, encoding='utf-8')
            books_articles.append((stem, f"{slug}.md"))
            print(f"  Converted docx: {stem}")
        except Exception as e:
            print(f"  Error converting {p.name}: {e}")

    elif p.suffix in ['.md', '.txt']:
        md_file = books_dest / f"{slug}.md"
        try:
            txt = p.read_text(encoding='utf-8', errors='ignore')
            if not txt.startswith('# '):
                txt = f"# {stem}\n\n" + txt
            md_file.write_text(txt, encoding='utf-8')
            books_articles.append((stem, f"{slug}.md"))
            print(f"  Copied text: {stem}")
        except Exception as e:
            print(f"  Error reading {p.name}: {e}")

# Index for Tennis Books
books_links = "\n".join([f"- [{title}]({filename})" for title, filename in sorted(books_articles, key=lambda x: x[0])])
books_index = f"""---
title: Tennis Books Collection
description: Cleaned, structured, and translated classic tennis books (Absolute Tennis, Vic Braden, Step-by-Step Tennis Skills, etc.).
---

# Tennis Books Collection

Total Books & Guides: {len(books_articles)}

---

## Books Index

{books_links}
"""
(books_dest / 'index.md').write_text(books_index, encoding='utf-8')

# Also update reference-library/index.md to include TFL Manuals and Tennis Books
ref_lib_index = docs / '08-reference-library' / 'index.md'
ref_lib_content = """---
title: Reference Library
description: Comprehensive collection of coauthored books, TFL manuals, classic tennis books, technical reference, training programs, player profiles, and rivalry analyses.
---

# Reference Library

Welcome to the Reference Library — the foundational repository for long-form manuals, classic books, technical reference guides, and player profiles.

---

## Sections

- **[Coauthored Books](coauthored-books/index.md)** — Complete handbook series co-authored by AI research models and domain experts.
- **[TFL Training Manuals](tfl-manuals/index.md)** — Official Tennis Future Lab (TFL) training manuals, scaffolds, and biomechanics guides.
- **[Tennis Books Collection](tennis-books/index.md)** — Cleaned, structured, and translated classic tennis books (Absolute Tennis, Vic Braden, Step-by-Step Tennis Skills).
- **[Technical Reference](technical-reference/index.md)** — Technical reference sheets, formulas, biomechanical data, and anatomical diagrams.
- **[Training Programs](training-programs/index.md)** — Periodized training programs, daily practice routines, and development roadmaps.
- **[Player Profiles](player-profiles/index.md)** — Technical and tactical breakdowns of ATP/WTA professional players.
- **[Rivalry Analyses](rivalry-analyses/index.md)** — In-depth analysis of legendary tennis rivalries and strategic matchups.
- **[Tennis Lexicon](tennis-lexicon/index.md)** — Dictionary of tennis terminology, biomechanical jargon, and strategic concepts.
"""
ref_lib_index.write_text(ref_lib_content, encoding='utf-8')

print("\nIntegration complete!")
