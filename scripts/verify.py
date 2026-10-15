"""Compare the rendered Markdown with the source OOXML text snapshot."""
from pathlib import Path
import hashlib, json, re
from bs4 import BeautifulSoup
import markdown
ROOT=Path(__file__).resolve().parents[1]
def norm(t):return re.sub(r'\s+','',t).replace('\ufe0e','')
for record in json.loads((ROOT/'verification/sources.json').read_text()):
    slug=record['page']
    md=(ROOT/'docs'/f'{slug}.md').read_text().split('<!-- source-content:start -->')[1].split('<!-- source-content:end -->')[0]
    html=markdown.markdown(md,extensions=['tables','attr_list','md_in_html'])
    soup=BeautifulSoup(html,'html.parser')
    for math in soup.select('math'):math.decompose()
    actual=norm(soup.get_text())
    expected=(ROOT/'verification'/f'{slug}.txt').read_text()
    assert actual==expected, f'{slug}: text differs ({len(actual)} vs {len(expected)} characters)'
    assert len(soup.select('table'))==record['tables'],f'{slug}: table count differs'
    full=BeautifulSoup(html,'html.parser')
    assert len(full.select('math'))==record['math'],f'{slug}: formula count differs'
    assert len(full.select('img'))==record['images'],f'{slug}: image count differs'
    for image in full.select('img'):
        assert (ROOT/'docs'/image['src']).is_file(),image['src']
    source=ROOT/'documents'/record['source']
    if source.exists():assert hashlib.sha256(source.read_bytes()).hexdigest()==record['sha256']
    print(f'PASS {slug}: {len(expected)} characters, {record["tables"]} tables, {record["math"]} MathML formulas, {record["images"]} images')

for name, digest in json.loads((ROOT/"verification/assets.json").read_text()).items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
print("PASS asset checksums")
