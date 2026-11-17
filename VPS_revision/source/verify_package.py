from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from lxml import etree as E
import json,re,subprocess

b=Path(__file__).resolve().parents[1]
mx=E.Element('mxfile',host='app.diagrams.net')
for p in sorted((b/'diagrams').glob('*.drawio')):
    r=E.parse(str(p)).getroot()
    for d in r:
        cells=d.findall('.//mxCell');ids=[n.get('id') for n in cells]
        assert len(ids)==len(set(ids)),p
        for c in cells:
            for attr in ['source','target','parent']:
                if c.get(attr):assert c.get(attr) in ids,(p,attr,c.get(attr))
        mx.append(d)
assert len(mx)==19
E.ElementTree(mx).write(str(b/'VPS_диаграммы.drawio'),encoding='UTF-8',xml_declaration=True)

with ZipFile(b/'VPS_project_исправленный.docx') as z:
    assert z.testzip() is None
    for p in z.namelist():
        if p.endswith('.xml') or p.endswith('.rels'):E.fromstring(z.read(p))
    root=E.fromstring(z.read('word/document.xml'));ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    texts=root.xpath('//w:t/text()',namespaces=ns)
    caps=[s for s in texts if re.match(r'(Рисунок|Таблица) \d+ — ',s)]
    for prefix,count in [('Рисунок',19),('Таблица',32)]:
        vals=[int(re.match(prefix+r' (\d+)',s)[1]) for s in caps if s.startswith(prefix)]
        assert vals==list(range(1,count+1)),(prefix,vals)
    relationships=E.fromstring(z.read('word/_rels/document.xml.rels'))
    for v in relationships:assert 'word/'+v.get('Target') in z.namelist(),v.get('Target')

report=json.loads((b/'work'/'layout_report.json').read_text())
assert len(report)==52 and all(p['scale']==1 for p in report)
subprocess.run(['pdftotext','-layout',str(b/'VPS_project_исправленный.pdf'),str(b/'work'/'revised.txt')],check=True)
s=(b/'work'/'revised.txt').read_text();pages=s.split('\f')
assert len(pages)==53
assert '\ufffd' not in s
for line in (b/'work'/'page_map.txt').read_text().splitlines():
    n,title=line.split(': ',1)
    if int(n)==1:continue
    normalize=lambda x:re.sub(r'\s+','',x)
    assert normalize(title) in normalize(pages[int(n)-1]),(n,title)

# Numbered architecture arrows match the step tables without missing numbers.
for prefix,total in [('16_',8),('17_',14),('18_',12),('19_',12)]:
    diagram=E.parse(str(next((b/'diagrams').glob(prefix+'*.drawio'))))
    nums=[int(v.get('value')) for v in diagram.findall('.//mxCell') if v.get('edge')=='1']
    assert sorted(nums)==list(range(1,total+1)),(prefix,nums)
# Sequence flows remain inside a participant; message flows cross participants.
flows=json.loads((b/'work'/'bpmn_flows.json').read_text())
assert len(flows)==3
for diagram in flows:
    for flow in diagram['flows']:
        cross=diagram['pools'][flow['source']]!=diagram['pools'][flow['target']]
        assert cross==flow['message'],(diagram['diagram'],flow)
    model=E.parse(str(b/'diagrams'/(diagram['diagram']+'.drawio')))
    by_id={cell.get('id'):cell for cell in model.findall('.//mxCell')}
    for flow in diagram['flows']:
        if flow['message']:
            for endpoint in ['source','target']:
                assert 'rhombus;' not in by_id[flow[endpoint]].get('style',''),flow
# Confirm the new flow dictionary is complete.
text='\n'.join(texts)
for i in range(1,38):assert f'F{i:02d}.' in text,i

with ZipFile(b/'VPS_исправленный_комплект.zip','w',ZIP_DEFLATED) as z:
    for p in sorted(b.rglob('*')):
        if p.is_file() and 'work' not in p.relative_to(b).parts and p.suffix!='.zip' and '__pycache__' not in p.parts:
            z.write(p,Path('VPS_revision')/p.relative_to(b))
    assert z.testzip() is None
print('Verified: 52 pages; 19 editable diagrams; 32 sequential tables; 19 sequential figures; valid DOCX relationships; contents matches PDF; no layout scaling.')
print('Archive bytes:',(b/'VPS_исправленный_комплект.zip').stat().st_size)
