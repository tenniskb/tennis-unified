"""Generate .md -> .html redirect HTML files for legacy URLs.

For every docs/<rel>.md we create site/<rel>.md as a small HTML redirect
pointing at site/<rel>.html.  Works on both Windows and POSIX runners.
"""
import pathlib
import shutil

# CWD-relative so this runs identically on Windows and on GitHub Actions.
REPO = pathlib.Path(__file__).resolve().parent
DOCS = REPO / "docs"
SITE = REPO / "site"
VI_SITE = SITE / "vi"

REDIRECT_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Redirecting...</title>
  <meta http-equiv="refresh" content="0; url={target_url}">
  <script>
    window.location.replace("{target_url}" + window.location.search + window.location.hash);
  </script>
</head>
<body>
  <p>Redirecting to <a href="{target_url}">{target_url}</a>...</p>
</body>
</html>"""


def emit_redirect(target: pathlib.Path, html_name: str) -> bool:
    """Write the redirect HTML file at `target` (an .md path inside site/)."""
    try:
        if target.is_dir():
            shutil.rmtree(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(REDIRECT_TEMPLATE.format(target_url=html_name), encoding="utf-8")
        return True
    except OSError as exc:
        print(f"Warning writing {target}: {exc}", flush=True)
        return False


def main() -> None:
    if not DOCS.is_dir():
        raise SystemExit(f"Docs directory not found: {DOCS}")
    if not SITE.is_dir():
        raise SystemExit(f"Site directory not found (run `mkdocs build` first): {SITE}")

    count = 0
    for md_path in DOCS.rglob("*.md"):
        if md_path.name == "404.md":
            continue
        rel = md_path.relative_to(DOCS)
        if md_path.name == "index.md":
            target_url = "index.html"
        else:
            target_url = md_path.name.replace(".md", ".html")

        if emit_redirect(SITE / rel, target_url):
            count += 1
        if VI_SITE.is_dir():
            emit_redirect(VI_SITE / rel, target_url)

    print(f"Successfully generated redirect files for {count} markdown sources.")


if __name__ == "__main__":
    main()
