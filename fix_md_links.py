"""Rewrite broken .md link references in OLD stub index files to point at
the corresponding .html URL wherever the target file actually lives.

Strategy
--------
For every .md file under docs/ we scan all `[label](target.md)` references
and check whether `target.md` exists in the same folder.  If not, we look
elsewhere in docs/ for a file with the same stem and pick the one that is
"closest" (preferring siblings of the same old stub -> new folder pair).
The rewritten target uses the .html extension so it renders correctly under
`use_directory_urls: false`.
"""
from __future__ import annotations

import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parent
DOCS = REPO / "docs"

# OLD stub -> NEW numbered folder pairings.  Used to disambiguate when
# multiple files share the same stem (e.g. en/vi duplicates).
OLD_TO_NEW = {
    "fundamentals": "01-fundamentals",
    "more": "02-more",
    "stroke-analysis": "03-stroke-analysis",
    "new-issue": "04-new-issue",
    "foundation": "03-foundation",
    "advanced": "04-advanced",
    "elite": "05-elite",
    "anatomy-lab": "06-anatomy-lab",
    "angle-atlas": "07-angle-atlas",
    "reference-library": "08-reference-library",
    "tennis-wiki-reference": "09-tennis-wiki-reference",
    "specialty-shots": "10-specialty-shots",
    "doubles": "11-doubles",
    "biomechanics-neurology": "12-biomechanics-neurology",
}

LINK_RE = re.compile(r"(!\[[^\]]*\]|\[[^\]]+\])\(([^)]+\.md)([^)]*)\)")


def build_stem_index() -> dict[str, list[pathlib.Path]]:
    """Map file stem -> list of paths that have that stem."""
    by_stem: dict[str, list[pathlib.Path]] = {}
    for f in DOCS.rglob("*.md"):
        if f.name == "404.md":
            continue
        by_stem.setdefault(f.stem, []).append(f)
    return by_stem


def pick_target(stem: str, source_md: pathlib.Path, candidates: list[pathlib.Path]) -> pathlib.Path | None:
    """Pick the best candidate when there are several files with the same stem."""
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]

    source_parts = source_md.relative_to(DOCS).parts

    # 1. Sibling in same numbered folder as source's parent (most common case)
    if len(source_parts) >= 2:
        sibling_stub = source_parts[1] if source_parts[0] == "" else source_parts[0]
        new_stub = OLD_TO_NEW.get(sibling_stub)
        if new_stub:
            for c in candidates:
                parts = c.relative_to(DOCS).parts
                if parts and parts[0] == new_stub:
                    return c

    # 2. Shortest path (top-level prefer)
    candidates.sort(key=lambda p: (len(p.relative_to(DOCS).parts), str(p)))
    return candidates[0]


def fix_file(md: pathlib.Path, stem_index: dict[str, list[pathlib.Path]]) -> tuple[int, int]:
    """Rewrite broken .md links inside `md`. Returns (rewrites, unresolved)."""
    try:
        text = md.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return 0, 0

    rewrites = 0
    unresolved = 0

    def repl(m: re.Match) -> str:
        nonlocal rewrites, unresolved
        label, target, suffix = m.group(1), m.group(2), m.group(3)
        if target.startswith(("http://", "https://", "/", "mailto:")):
            return m.group(0)
        # Local file
        target_path = (md.parent / target).resolve()
        if target_path.exists():
            # Link already works; rewrite .md -> .html anyway for safety
            new_target = target.rsplit(".", 1)[0] + ".html"
            rewrites += 1
            return f"{label}({new_target}{suffix})"
        # Try to find by stem
        stem = pathlib.Path(target).stem
        candidates = stem_index.get(stem, [])
        best = pick_target(stem, md, candidates)
        if best is None:
            unresolved += 1
            return m.group(0)
        # Build relative URL from md.parent to best (with .html extension)
        rel = best.relative_to(md.parent.parent.parent.parent.parent) if False else None  # placeholder
        # Compute relative path from md's parent to best, then replace .md with .html
        try:
            rel_path = pathlib.Path(*best.relative_to(md.parent).parts)
            rel_str = str(rel_path.with_suffix(".html")).replace("\\", "/")
            rewrites += 1
            return f"{label}({rel_str}{suffix})"
        except ValueError:
            # best is not under md.parent's parent... build from DOCS root
            doc_rel = best.relative_to(DOCS)
            doc_rel_str = str(doc_rel.with_suffix(".html")).replace("\\", "/")
            # Need to count ../ needed
            depth = len(md.parent.relative_to(DOCS).parts)
            prefix = "../" * depth
            rewrites += 1
            return f"{label}({prefix}{doc_rel_str}{suffix})"

    new_text = LINK_RE.sub(repl, text)
    if new_text != text:
        md.write_text(new_text, encoding="utf-8")
    return rewrites, unresolved


def main() -> None:
    stem_index = build_stem_index()
    md_files = list(DOCS.rglob("*.md"))
    md_files = [f for f in md_files if f.name != "404.md"]
    total_rewrites = 0
    total_unresolved = 0
    files_changed = 0
    for md in md_files:
        rewrites, unresolved = fix_file(md, stem_index)
        if rewrites > 0 or unresolved > 0:
            files_changed += 1 if rewrites > 0 else 0
            total_rewrites += rewrites
            total_unresolved += unresolved
    print(f"Files scanned: {len(md_files)}")
    print(f"Files rewritten: {files_changed}")
    print(f"Total .md -> .html rewrites: {total_rewrites}")
    print(f"Unresolved links (no candidate): {total_unresolved}")


if __name__ == "__main__":
    main()
