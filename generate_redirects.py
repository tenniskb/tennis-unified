import pathlib, os
repo = pathlib.Path(r'C:/Users/Henry/Documents/GitHub/tennis-unified')
docs = repo/'docs'
site = repo/'site'
redirect_template = '''<!DOCTYPE html><html><head><meta http-equiv="refresh" content="0; url=/{dest}/" /></head><body>Redirecting…</body></html>'''
for md_path in docs.rglob('*.md'):
    rel = md_path.relative_to(docs)
    # URL path without .md
    dest = str(rel.with_suffix('')).replace('\\','/')
    # target redirect file path in site
    redirect_path = site/(dest+'.md.html')
    redirect_path.parent.mkdir(parents=True, exist_ok=True)
    redirect_path.write_text(redirect_template.format(dest=dest), encoding='utf-8')
print('Redirect files generated')
