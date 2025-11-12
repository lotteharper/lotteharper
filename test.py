from bs4 import BeautifulSoup

html = "<div><p>Text 1</p><b>Text 2</b><p>Text 3</p></div>"
soup = BeautifulSoup(html, 'html.parser')

from django.utils.html import strip_tags
for tag in soup.find_all(string=True):
    if tag.parent.name not in ['script', 'style', 'pre', 'code'] and tag.string:
        print(strip_tags(str(tag.string)))
