"""Render the generated OOXML with system Pango/Cairo, without network dependencies."""
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
import cairo,gi,json
gi.require_version('Pango','1.0');gi.require_version('PangoCairo','1.0')
from gi.repository import Pango,PangoCairo

BASE=Path(__file__).resolve().parents[1]
W,H=595.276,841.89
M=56.7; TOP=45; BOTTOM=45; CW=W-2*M
N={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main','wp':'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
def wt(n):
    parts=[]
    for v in n.iter():
        if v.tag=='{'+N['w']+'}t':parts.append(v.text or '')
        elif v.tag=='{'+N['w']+'}br':parts.append('\n')
    return ''.join(parts)
def color(c):return tuple(int(c[i:i+2],16)/255 for i in (0,2,4))
def text(ctx,t,x,y,width,size=12,bold=False,align='left',col='0f172a',spacing=1):
    layout=PangoCairo.create_layout(ctx)
    font=Pango.FontDescription(('Liberation Serif Bold' if bold else 'Liberation Serif')+' '+str(size))
    layout.set_font_description(font);layout.set_width(int(width*Pango.SCALE));layout.set_text(t,-1)
    layout.set_spacing(int(spacing*Pango.SCALE));layout.set_wrap(Pango.WrapMode.WORD_CHAR)
    layout.set_alignment({'left':Pango.Alignment.LEFT,'center':Pango.Alignment.CENTER,'right':Pango.Alignment.RIGHT}[align])
    # Set resolution so font sizes are PDF points.
    PangoCairo.context_set_resolution(layout.get_context(),72)
    ctx.set_source_rgb(*color(col));ctx.move_to(x,y);PangoCairo.show_layout(ctx,layout)
    _,logical=layout.get_extents();return logical.height/Pango.SCALE

with ZipFile(BASE/'VPS_project_исправленный.docx') as z:
    doc=E.fromstring(z.read('word/document.xml'))
    rel=E.fromstring(z.read('word/_rels/document.xml.rels'))
    paths={n.get('Id'):n.get('Target') for n in rel}
    groups=[[]]
    for n in doc.find('w:body',N):
        if n.tag.endswith('sectPr'):continue
        if n.find('w:pPr/w:pageBreakBefore',N) is not None:groups.append([])
        groups[-1].append(n)
    surfaces=[];stats=[]
    for page_no,nodes in enumerate(groups,1):
        surf=cairo.RecordingSurface(cairo.CONTENT_COLOR_ALPHA,None);ctx=cairo.Context(surf);y=0
        for n in nodes:
            if n.tag.endswith('tbl'):
                widths=[int(v.get('{'+N['w']+'}w'))/9638*CW for v in n.findall('w:tblGrid/w:gridCol',N)]
                for ri,tr in enumerate(n.findall('w:tr',N)):
                    heights=[];cells=tr.findall('w:tc',N)
                    for cell,cw in zip(cells,widths):
                        tmp=cairo.RecordingSurface(cairo.CONTENT_COLOR_ALPHA,None);tc=cairo.Context(tmp)
                        heights.append(text(tc,wt(cell),0,0,cw-9,10.5,ri==0,spacing=.3))
                    rh=max(heights)+9;x=0
                    for cell,cw in zip(cells,widths):
                        ctx.set_source_rgb(*color('e2e8f0' if ri==0 else 'f8fafc' if ri%2 else 'ffffff'));ctx.rectangle(x,y,cw,rh);ctx.fill_preserve();ctx.set_source_rgb(*color('cbd5e1'));ctx.set_line_width(.45);ctx.stroke()
                        text(ctx,wt(cell),x+4.5,y+4.5,cw-9,10.5,ri==0,spacing=.3);x+=cw
                    y+=rh
                y+=3;continue
            drawing=n.find('.//w:drawing',N)
            if drawing is not None:
                blip=n.find('.//a:blip',N);rid=blip.get('{'+N['r']+'}embed');path=BASE/'diagrams'/Path(paths[rid]).name
                ex=n.find('.//wp:extent',N);iw=int(ex.get('cx'))/12700;ih=int(ex.get('cy'))/12700
                im=cairo.ImageSurface.create_from_png(str(path));ctx.save();ctx.translate((CW-iw)/2,y);ctx.scale(iw/im.get_width(),ih/im.get_height());ctx.set_source_surface(im,0,0);ctx.paint();ctx.restore();y+=ih+5;continue
            style=n.find('w:pPr/w:pStyle',N);style=style.get('{'+N['w']+'}val') if style is not None else 'Normal'
            if style=='TOCField':continue
            t=wt(n);align=n.find('w:pPr/w:jc',N);align=align.get('{'+N['w']+'}val') if align is not None else 'left'
            if align=='both':align='left'
            sz=n.find('.//w:rPr/w:sz',N);sz=float(sz.get('{'+N['w']+'}val'))/2 if sz is not None else None
            bold=n.find('.//w:rPr/w:b',N) is not None
            if style in ('Heading1','TOCHeading'):size=16;before=0;after=10.5;bold=True
            elif style=='Heading2':size=13.5;before=8;after=5.5;bold=True
            elif style=='Caption':size=10.5;before=4;after=5;align='center'
            elif style=='TOCText':size=9.5;before=0;after=1.5
            else:size=sz or 12;before=0;after=6.25
            y+=before
            if not t:y+=size+after;continue
            hh=text(ctx,t,0,y,CW,size,bold,align,'475569' if style=='Caption' else '0f172a',spacing=.8 if style=='Normal' else .3)
            y+=hh+after
        scale=min(1,(H-TOP-BOTTOM-10)/y)
        surfaces.append((surf,scale));stats.append({'page':page_no,'content_height_pt':round(y,1),'scale':round(scale,3),'title':wt(nodes[0])})
    out=BASE/'VPS_project_исправленный.pdf';pdf=cairo.PDFSurface(str(out),W,H)
    pdf.set_metadata(cairo.PDF_METADATA_TITLE,'Информационная система «Аренда виртуальных серверов VPS/VDS»')
    pdf.set_metadata(cairo.PDF_METADATA_AUTHOR,'Чигрин Н.А.; Ефимовых М.А.; Заживихин К.А.')
    pdf.set_metadata(cairo.PDF_METADATA_SUBJECT,'Проектная документация: данные, процессы, архитектура и оценка качества')
    c=cairo.Context(pdf)
    for i,(s,sc) in enumerate(surfaces,1):
        pdf.add_outline(cairo.PDF_OUTLINE_ROOT,stats[i-1]['title'],f'page={i}',cairo.PDF_OUTLINE_FLAG_OPEN)
        c.set_source_rgb(1,1,1);c.paint();c.save();c.translate(M,TOP);c.scale(sc,sc);c.set_source_surface(s,0,0);c.paint();c.restore()
        if i>1:text(c,str(i),0,H-32,W,10,align='center',col='475569')
        pdf.show_page()
    pdf.finish();(BASE/'work'/'layout_report.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2))
    print('PDF:',out,'pages:',len(groups),'minimum scale:',min(s for _,s in surfaces))
    print('Scaled pages:',[(s['page'],s['scale']) for s in stats if s['scale']<1])
