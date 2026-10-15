"""One-time DOCX import. Requires local documents/; never rewrites source files."""
from pathlib import Path
import hashlib, json, re, zipfile
from lxml import etree as ET
from bs4 import BeautifulSoup
import pypandoc

ROOT = Path(__file__).resolve().parents[1]
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

def normalized(text):
    return re.sub(r'\s+', '', text).replace('\ufe0e', '')

def source_text(root):
    return ''.join(n.text or '' if n.tag == '{'+W+'}t' else '\u2011' if n.tag == '{'+W+'}noBreakHyphen' else '' for n in root.iter())

def main():
    records=[]
    documents={}
    for file in sorted((ROOT/'documents').glob('*.docx')):
        slug = 'evaluation' if '№ 5' in file.name else 'technical-specification'
        media = f'docs/assets/{slug}'
        html = pypandoc.convert_file(str(file), 'html5', extra_args=['--mathml',f'--extract-media={media}'])
        soup = BeautifulSoup(html, 'html.parser')
        for image in soup.select('img'):
            image['src'] = image['src'].removeprefix('docs/')
            if image['src'].endswith('.wmf'):
                image['src'] = image['src'][:-4]+'.png'
                assert (ROOT/'docs'/image['src']).exists(), 'Render WMF formulas to PNG first'
            image['alt'] = 'Формула из исходного документа' if slug=='evaluation' else 'Схема из технического задания'
        for table in list(soup.select('table')):
            wrap=soup.new_tag('div',attrs={'class':'source-table'})
            table.wrap(wrap)
        # Use real source headings for MkDocs TOC, retaining Pandoc anchor identifiers.
        for heading in list(soup.find_all(re.compile('^h[1-6]$'))):
            if not heading.get_text().strip():
                heading.decompose()
                continue
            level=min(int(heading.name[1])+1,6)
            title=heading.get_text().replace('\n',' ')
            heading.replace_with(f'\n\n'+ '#' * level + ' '+title+f' {{#{heading.get("id")}}}\n\n')
        title='Порядок оценки' if slug=='evaluation' else 'Техническое задание'
        navigation=''
        if slug=='evaluation':
            entries=[]
            starts=['Информация о заказчике', 'Критерии и показатели', 'Отдельные положения']
            for idx,start in enumerate(starts,1):
                target=next(p for p in soup.select('p') if p.get_text(' ',strip=True).startswith(start))
                target['id']=f'section-{idx}'
                label=' '.join(target.get_text(' ',strip=True).split())
                entries.append(f'- [{label}](#section-{idx})')
            navigation='\n'.join(entries)+'\n\n'
        output=f'# {title}\n\n'+navigation+'<!-- source-content:start -->\n'+str(soup)+'\n<!-- source-content:end -->\n'
        documents[slug]=output
        with zipfile.ZipFile(file) as z:
            root=ET.fromstring(z.read('word/document.xml'))
            for name in ('word/footnotes.xml','word/endnotes.xml'):
                if name in z.namelist():
                    notes=ET.fromstring(z.read(name))
                    assert not normalized(source_text(notes)), 'Nonempty notes need explicit import'
            text=normalized(source_text(root))
            (ROOT/'verification'/f'{slug}.txt').write_text(text)
            records.append({'source':file.name,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'page':slug,'text_characters':len(text),'tables':len(root.findall('.//{'+W+'}tbl')),'math':len(root.findall('.//{http://schemas.openxmlformats.org/officeDocument/2006/math}oMath')),'images':len(soup.select('img'))})
    from split_documents import write_documents
    write_documents(documents)
    (ROOT/'verification/sources.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
