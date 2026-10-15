"""Split imported documents without changing their source text or table markup."""
from pathlib import Path
import json,re
from urllib.parse import unquote
import yaml
ROOT=Path(__file__).resolve().parents[1]
START='<!-- source-content:start -->'
END='<!-- source-content:end -->'

def corpus(md):return md.split(START,1)[1].split(END,1)[0].strip()
def title(line):return re.sub(r'\s*\{#[^}]+\}\s*$','',re.sub(r'^#+\s*','',line)).strip()
def write_documents(documents):
    pages={}; anchor_maps={}; nav=[]
    for slug,md in documents.items():
        body=corpus(md); entries=[]; fragments=[]; anchors={}
        def add(path,label,content,level=0):
            # Heading promotion affects markup only; all source words stay in place.
            content=re.sub(r'^(#{2,6})(?= )',lambda m:'#'*max(1,len(m[1])-level),content,flags=re.M)
            content=content.replace('src="assets/', 'src="/assets/')
            fragment={'path':path,'title':label,'content':content}
            fragments.append(fragment)
            for match in re.finditer(r'\{#([^}]+)\}|\bid="([^"]+)"',content):
                anchors[match[1] or match[2]]=path
            return fragment
        if slug=='technical-specification':
            chunks=re.split(r'(?=^## )',body,flags=re.M)
            add(f'{slug}.md','Техническое задание',chunks[0])
            for chunk in chunks[1:]:
                label=title(chunk.splitlines()[0])
                appendix=re.match(r'Приложение № (\d+)',label)
                number=re.match(r'(\d+)\.',label)
                stem=f'appendix-{int(appendix[1]):02d}' if appendix else f'{int(number[1]):02d}'
                path=f'{slug}/{stem}.md'
                if number and int(number[1]) in (9,15):
                    n=number[1]
                    subs=re.split(rf'(?=^### {n}\.\d+\.?\s)',chunk,flags=re.M)
                    parent=add(path,label,subs[0],1);children=[]
                    for sub in subs[1:]:
                        sublabel=title(sub.splitlines()[0]); subnum=re.match(r'\d+\.(\d+)',sublabel)[1]
                        subpath=f'{slug}/{stem}-{int(subnum):02d}.md'
                        add(subpath,sublabel,sub,2);children.append({sublabel:subpath})
                    parent['children']=children
                    entries.append({label:[{'Обзор':path}]+children})
                else:
                    add(path,label,chunk,1);entries.append({label:path})
        else:
            # Section I lives inside the first source table: keep that table intact.
            chunks=re.split(r'(?=<ol start="[23]" type="I">)',body)
            assert len(chunks)==3
            labels=['I. Информация о заказчике и закупке','II. Критерии и показатели оценки','III. Отдельные положения о применении критериев оценки']
            for i,(label,chunk) in enumerate(zip(labels,chunks),1):
                path=f'{slug}/{i:02d}.md'
                add(path,label,chunk)
                entries.append({label:path})
        pages[slug]=[f['path'] for f in fragments]
        anchor_maps[slug]={anchor:path.removesuffix('.md')+'/#'+anchor for anchor,path in anchors.items()}
        links=[]
        for entry in entries:
            label,value=next(iter(entry.items()))
            path=next(iter(value[0].values())) if isinstance(value,list) else value
            links.append(f'- [{label}]({path})')
            if isinstance(value,list):
                for child in value[1:]:
                    cl,cp=next(iter(child.items()));links.append(f'    - [{cl}]({cp})')
        overview_title='Техническое задание' if slug=='technical-specification' else 'Порядок оценки'
        overview=f'# {overview_title}\n\nОглавление документа. Выберите раздел; поиск работает по всем страницам.\n\n'+'\n'.join(links)+'\n\n'
        for fragment in fragments:
            path=fragment['path'];prefix=''
            if path==f'{slug}.md':prefix=overview
            elif slug=='evaluation':prefix=f'# {fragment["title"]}\n\n'
            text=prefix+START+'\n'+fragment['content']+'\n'+END+'\n'
            if fragment.get('children'):
                text+='\n## Подразделы\n\n'
                for child in fragment['children']:
                    cl,cp=next(iter(child.items()));text+=f'- [{cl}]({Path(cp).name})\n'
            dest=ROOT/'docs'/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text)
        if slug=='evaluation':(ROOT/'docs'/f'{slug}.md').write_text(overview)
        nav.append({overview_title:[{'Оглавление':f'{slug}.md'}]+entries})
    # Repair any source fragment links which now point to a different page.
    import posixpath
    for slug,group in pages.items():
        for path in group:
            dest=ROOT/'docs'/path;text=dest.read_text()
            def relocate(match):
                anchor=unquote(match[1]);target=anchor_maps[slug].get(anchor)
                if not target:return match[0]
                targetpath=target.split('/#')[0]+'.md'
                if targetpath==path:return match[0]
                return 'href="'+posixpath.relpath(targetpath,posixpath.dirname(path) or '.')+'#'+match[1]+'"'
            dest.write_text(re.sub(r'href="#([^"]+)"',relocate,text))
    (ROOT/'verification/pages.json').write_text(json.dumps(pages,ensure_ascii=False,indent=2)+'\n')
    # Keep existing bookmarks to the former single-page documents usable.
    scripts=ROOT/'docs/javascripts';scripts.mkdir(exist_ok=True)
    redirects={}
    for slug,anchors in anchor_maps.items():
        redirects['/'+slug+'/']={'#'+k:'/'+v for k,v in anchors.items() if v.split('/#')[0]!=slug}
    js='// Preserve bookmarks created before the documents were split.\n'
    js+='const documentRedirects = '+json.dumps(redirects,ensure_ascii=False)+';\n'
    js+='function redirectDocumentAnchor() {\n  const target = documentRedirects[location.pathname]?.[decodeURIComponent(location.hash)];\n  if (target) location.replace(target);\n}\nredirectDocumentAnchor();\nwindow.addEventListener("hashchange", redirectDocumentAnchor);\n'
    (scripts/'document-redirects.js').write_text(js)
    config=yaml.safe_load((ROOT/'mkdocs.yml').read_text())
    config['nav']=[{'Главная':'index.md'}]+nav
    config['extra_javascript']=['javascripts/document-redirects.js']
    for feature in ['navigation.indexes','navigation.path','navigation.footer']:
        if feature not in config['theme']['features']:config['theme']['features'].append(feature)
    (ROOT/'mkdocs.yml').write_text(yaml.safe_dump(config,allow_unicode=True,sort_keys=False))

if __name__=='__main__':
    from import_documents import main
    main()
