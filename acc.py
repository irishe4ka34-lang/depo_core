import zipfile,sys,copy,re
from lxml import etree
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
q=lambda t:'{%s}%s'%(W,t)
def load(path):
    root=etree.fromstring(zipfile.ZipFile(path).read('word/document.xml'))
    for e in list(root.iter(q('del'))):
        p=e.getparent()
        if p.tag==q('rPr'): continue
        if p.tag==q('trPr'):
            tr=p.getparent(); tr.getparent().remove(tr); continue
        p.remove(e)
    for tr in list(root.iter(q('tr'))):
        pass
    return root.find(q('body'))
def txt(e): return ''.join(t.text or '' for t in e.iter(q('t')))
def style(p):
    s=p.find(q('pPr')+'/'+q('pStyle')); return s.get(q('val')) if s is not None else ''
def section(body,prefix):
    out=[];on=False
    for e in body:
        if e.tag==q('p') and style(e)=='Heading1':
            if on: break
            on=txt(e).startswith(prefix)
            continue
        if on: out.append(e)
    return out
def dump(els):
    lines=[]
    for e in els:
        if e.tag==q('p'):
            t=txt(e)
            if t.strip(): lines.append(('H2 ' if style(e)=='Heading2' else '')+t)
        elif e.tag==q('tbl'):
            for tr in e.findall(q('tr')): lines.append(' | '.join(txt(tc) for tc in tr.findall(q('tc'))))
    return '\n'.join(lines)
