import pathlib, os, shutil

repo = pathlib.Path(r'C:/Users/Henry/Documents/GitHub/tennis-unified')
docs = repo / 'docs'
site = repo / 'site'

redirect_template = '''<!DOCTYPE html>
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
</html>'''

count = 0
for md_path in docs.rglob('*.md'):
    if md_path.name == '404.md':
        continue

    rel = md_path.relative_to(docs)
    rel_str = str(rel).replace('\\', '/')
    stem_str = str(rel.with_suffix('')).replace('\\', '/')
    html_name = md_path.name.replace('.md', '.html')
    
    # 1. English site redirects
    # Create HTML file at site/.../filename.md
    file_redirect = site / rel
    try:
        if file_redirect.is_dir():
            shutil.rmtree(file_redirect)
        file_redirect.parent.mkdir(parents=True, exist_ok=True)
        file_redirect.write_text(redirect_template.format(target_url=html_name), encoding='utf-8')
    except Exception as e:
        print(f"Warning writing {file_redirect}: {e}")

    # Create HTML file at site/.../filename.md/index.html (directory)
    # Note: On Windows, file_redirect and dir_redirect cannot both have the name filename.md.
    # So if filename.md is a file, we create site/.../filename.md_redirect/index.html or site/.../filename.md.html
    # But since file_redirect site/.../filename.md ALREADY exists as an HTML redirect file,
    # requesting .../filename.md is served directly by GitHub Pages as that redirect file!

    # 2. Vietnamese site redirects (if site/vi exists)
    vi_site = site / 'vi'
    if vi_site.exists():
        vi_file = vi_site / rel
        try:
            if vi_file.is_dir():
                shutil.rmtree(vi_file)
            vi_file.parent.mkdir(parents=True, exist_ok=True)
            vi_file.write_text(redirect_template.format(target_url=html_name), encoding='utf-8')
        except Exception as e:
            print(f"Warning writing {vi_file}: {e}")
        
    count += 1

print(f'Successfully generated redirect files for {count} markdown sources.')
