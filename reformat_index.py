import pathlib, sys
from bs4 import BeautifulSoup
site_path = pathlib.Path(r'C:/Users/Henry/Documents/GitHub/tennis-unified/site')
index_file = site_path / 'index.html'
backup = index_file.with_suffix('.bak.html')
# backup
index_file.rename(backup)
html = index_file.read_text(encoding='utf-8')
soup = BeautifulSoup(html, 'html5lib')
pretty = soup.prettify()
index_file.write_text(pretty, encoding='utf-8')
print('Backup created at', backup)
print('Reformatted written to', index_file)
