#!/usr/bin/env python3
"""Extract full text + embedded images from Step_by_Step_Tennis_Skills.pdf.

Page structure: each page contains ONE embedded raster image that covers the
entire page (2500x3600 px). The page text is overlaid on top of this image.
Numbered photographs appear within the single raster image, so each page is
its own "image unit" — extracting the embedded image captures all the photos
on that page without duplication.

Image handling:
- Extract embedded images only (no full-page renders — would be duplicate).
- Embedded images are typically 2500x3600 px so they preserve all numbered
  photos at full resolution.

Output:
- docs/08-reference-library/tennis-books/step-by-step-tennis-skills/assets/originals/<page>.png
- docs/08-reference-library/tennis-books/step-by-step-tennis-skills/en/<section>.md
"""

import re
import fitz
from pathlib import Path

REPO = Path(r"C:\Users\Henry\Documents\GitHub\tennis-unified")
PDF = Path(r"C:\Users\Henry\Documents\New Tennis Knowledge\Tennis Books\Step_by_Step_Tennis_Skills.pdf")
BOOK_DIR = REPO / "docs" / "08-reference-library" / "tennis-books" / "step-by-step-tennis-skills"
ASSETS_DIR = BOOK_DIR / "assets" / "originals"


# Section page ranges (1-indexed, inclusive) + slug + out_path (under en/)
SECTIONS = [
    ("Foreword",                                8,   10, "foreword.md"),
    ("Analysing Movements",                    13,  16, "basics/analysing-movements.md"),
    ("Tactics",                                17,  17, "basics/tactics.md"),
    ("Common Elements",                        18,  26, "basics/common-elements.md"),
    ("Breakdown of Stroke Techniques",         27,  28, "basics/breakdown-of-stroke-techniques.md"),
    ("Ground Strokes",                         30,  42, "strokes/ground-strokes.md"),
    ("Topspin",                                44,  54, "strokes/topspin.md"),
    ("Slicing",                                56,  64, "strokes/slicing.md"),
    ("Lobbing",                                66,  78, "strokes/lobbing.md"),
    ("Serving",                                80,  89, "strokes/serving.md"),
    ("Smashing",                               92, 102, "strokes/smashing.md"),
    ("Volleying",                             104, 112, "strokes/volleying.md"),
    ("Drop Shots",                            114, 120, "strokes/drop-shots.md"),
    ("Half Volleying",                        122, 125, "strokes/half-volleying.md"),
    ("Variations",                            126, 128, "strokes/variations.md"),
    ("Vital Groundwork",                      130, 134, "footwork/vital-groundwork.md"),
    ("Starting Positions",                    135, 136, "footwork/starting-positions.md"),
    ("Take-off and Running",                  137, 139, "footwork/takeoff-running.md"),
    ("Footwork at the Moment of Impact",      140, 144, "footwork/impact-footwork.md"),
    ("Returning to the Starting Position",    145, 148, "footwork/recovery.md"),
]


def extract_embedded_images(doc, max_width=1024):
    """Extract every embedded image, resized to max_width for web display.

    The PDF embeds one full-page raster per page (2500x3600 px native,
    ~5-20 MB each = 1.4 GB total at 148 pages). We downscale to 1024 px
    wide for web-display, which keeps all numbered photographs legible
    while cutting total payload to ~10-20 MB.
    """
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    page_images = {}
    total = 0
    for page_idx in range(doc.page_count):
        imgs = doc[page_idx].get_images(full=True)
        for img_idx, img in enumerate(imgs):
            xref = img[0]
            try:
                pix = fitz.Pixmap(doc, xref)
                if pix.alpha:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                # Downscale if wider than max_width
                if pix.width > max_width:
                    scale = max_width / pix.width
                    h = int(pix.height * scale)
                    mat = fitz.Matrix(scale, scale)
                    pix = fitz.Pixmap(pix, 0)  # ensure copy
                    # Use Pillow for fast resize if available
                    try:
                        from PIL import Image
                        import io
                        img_bytes = pix.tobytes("png")
                        with Image.open(io.BytesIO(img_bytes)) as pil_img:
                            pil_img.thumbnail((max_width, 99999), Image.LANCZOS)
                            fname = f"page{page_idx+1:03d}.png"
                            pil_img.save(str(ASSETS_DIR / fname), optimize=True)
                    except ImportError:
                        # Fallback: save full-res (will be larger)
                        fname = f"page{page_idx+1:03d}.png"
                        pix.save(str(ASSETS_DIR / fname))
                else:
                    fname = f"page{page_idx+1:03d}.png"
                    pix.save(str(ASSETS_DIR / fname))
                page_images[page_idx] = fname
                total += 1
                pix = None
            except Exception as e:
                print(f"  [WARN] p{page_idx+1} img{img_idx}: {e}")
    print(f"  Embedded images extracted: {total}")
    return page_images


def clean_text(raw: str) -> str:
    """Clean OCR artifacts and rewrap paragraphs.

    The PDF text is column-wrapped (each visual line is a separate newline),
    which makes it look fragmented in markdown. We rewrap by joining lines
    within each paragraph (blank-line separated paragraphs stay separate).
    """
    if not raw:
        return ""
    text = raw
    # Bullet artifacts from OCR
    text = re.sub(r"\be\b", "•", text)
    text = re.sub(r"@@+", "•", text)
    text = re.sub(r"\bee\b", "•", text)
    text = re.sub(r"\bean I a ee EE\bed\b", "•", text)
    # Normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)
    # Split into paragraphs (blank-line separated)
    paragraphs = re.split(r"\n\s*\n", text)
    out = []
    for p in paragraphs:
        lines = [ln.strip() for ln in p.split("\n") if ln.strip()]
        joined = " ".join(lines)
        if joined:
            out.append(joined)
    return "\n\n".join(out).strip()


def section_to_markdown(doc, page_images, start_p, end_p, title):
    """Build markdown content for pages start..end (1-indexed)."""
    parts = [f"# {title}", ""]
    parts.append(f"*Source: Step by Step Tennis Skills (Deutscher Tennis Bund), pages {start_p}–{end_p}.*")
    parts.append("")
    parts.append("---")
    parts.append("")

    for page_num in range(start_p, end_p + 1):
        page_idx = page_num - 1
        if page_idx >= doc.page_count:
            continue
        page = doc[page_idx]

        text = clean_text(page.get_text())
        if text:
            parts.append(f"## Page {page_num}")
            parts.append("")
            parts.append(text)
            parts.append("")

        if page_idx in page_images:
            parts.append(f"![Illustration page {page_num}](../assets/originals/{page_images[page_idx]})")
            parts.append("")

    return "\n".join(parts)


def main():
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(PDF))
    print(f"PDF: {doc.page_count} pages | {(PDF.stat().st_size / 1e6):.1f} MB\n")

    print("[1/2] Extracting embedded images...")
    page_images = extract_embedded_images(doc)

    print("\n[2/2] Building per-section markdown files...")
    for section_title, start_p, end_p, rel_path in SECTIONS:
        target = BOOK_DIR / "en" / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        md = section_to_markdown(doc, page_images, start_p, end_p, section_title)
        target.write_text(md, encoding="utf-8")
        words = len(md.split())
        chars = len(md)
        print(f"  [OK] {section_title:<40} p{start_p:>3}-{end_p:<3} ({words:>5,}w / {chars:>7,}c) -> en/{rel_path}")

    doc.close()

    print(f"\n=== DONE ===")
    print(f"Images: {len(page_images)} files  ->  {ASSETS_DIR}/")
    print(f"Markdown sections: {len(SECTIONS)} files  ->  {BOOK_DIR}/en/")


if __name__ == "__main__":
    main()