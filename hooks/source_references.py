"""Build-time source links and short, plain-text previews; no extra browser requests."""
from pathlib import Path
import re
from urllib.parse import urljoin, urlsplit, unquote
from bs4 import BeautifulSoup
import markdown

_sources = {}
_previews = {}

def on_files(files, config, **kwargs):
    _sources.clear()
    _previews.clear()
    for file in files:
        if file.src_uri.endswith('.md') and file.src_uri.startswith(('technical-specification', 'evaluation')):
            _sources['/'+file.url] = Path(file.abs_src_path)

def scenario_anchors(soup):
    for row in soup.select('tr'):
        first=row.find(['td','th'], recursive=False)
        if first:
            match=re.fullmatch(r'С-(\d+)',first.get_text(strip=True))
            if match:row['id']='scenario-c-'+match[1]

def preview(path, fragment):
    key=(path,fragment)
    if key in _previews:return _previews[key]
    html=markdown.markdown(_sources[path].read_text(), extensions=['tables','attr_list','md_in_html'])
    soup=BeautifulSoup(html,'html.parser')
    scenario_anchors(soup)
    node=soup.find(id=fragment) if fragment else None
    if node is None:
        node=soup.find(re.compile(r'^h[1-6]$'))
    if node and node.name=='span':
        node=node.find_parent('p') or node
    title=node.get_text(' ',strip=True) if node else 'Документ закупки'
    title=title or 'Документ закупки'
    parts=[]
    if node and node.name=='tr':
        cells=node.find_all(['td','th'],recursive=False)
        title=cells[1].get_text(' ',strip=True) if len(cells)>1 else title
        parts=[cells[-1].get_text(' ',strip=True)]
    elif node:
        level=int(node.name[1]) if re.fullmatch(r'h[1-6]',node.name or '') else 0
        if not level:parts.append(node.get_text(' ',strip=True))
        for sibling in node.next_siblings:
            name=getattr(sibling,'name',None)
            if not name:continue
            if level and re.fullmatch(r'h[1-6]',name) and int(name[1])<=level:break
            parts.append(sibling.get_text(' ',strip=True))
            if len(' '.join(parts))>1800:break
    text=re.sub(r'\s+',' ',' '.join(parts)).strip()
    if len(text)>1400:text=text[:1400].rsplit(' ',1)[0]+'…'
    result=(title,text)
    _previews[key]=result
    return result

def on_post_page(output, page, config, **kwargs):
    soup=BeautifulSoup(output,'html.parser')
    article=soup.select_one('article')
    if not article:return output
    scenario_anchors(article)
    for link in article.select('a[href]'):
        if 'headerlink' in link.get('class',[]):continue
        target=urlsplit(urljoin('https://docs.local/'+page.url,link['href']))
        path=unquote(target.path)
        if target.netloc!='docs.local' or path not in _sources:continue
        link['target']='_blank'
        link['rel']=['noopener','noreferrer']
        # Whole-document links may open a document, but have no useful excerpt.
        if path in ('/technical-specification/','/evaluation/'):
            continue
        title,text=preview(path,unquote(target.fragment))
        link['class']=list(link.get('class',[]))+['source-reference']
        link['data-source-title']=title
        link['data-source-excerpt']=text
    return str(soup)

def on_page_markdown(markdown, page, config, **kwargs):
    if page.file.src_uri.startswith('technical-specification'):
        return re.sub(r'<tr>(\s*<td[^>]*>)С-(\d+)(</td>)',
                      lambda m: '<tr id="scenario-c-'+m[2]+'">'+m[1]+'С-'+m[2]+m[3], markdown)
    return markdown
