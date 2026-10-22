"""Автоперенос модели, правил и справочников из docx (принятый вид) в файлы пилота."""
import sys, re, os, yaml, zipfile, copy
sys.path.insert(0, os.path.dirname(__file__))
from acc import load, section, q, style
from lxml import etree

R = os.path.join(os.path.dirname(__file__), 'repo')
b3 = load('/home/claude/work/ed8/out/03_Модель_данных_и_справочники.docx')
b4 = load('/home/claude/work/ed8/out/04_Правила_учёта_и_состояния.docx')
LABEL = re.compile(r'^1\.4 · [^.]+\.\s*')

def ptext(p):
    out = []
    for e in p.iter(q('t'), q('br'), q('tab')):
        out.append('\n' if e.tag == q('br') else ' ' if e.tag == q('tab') else (e.text or ''))
    return ''.join(out).strip()

def ctext(tc):
    return '\n'.join(x for x in (ptext(p) for p in tc.findall(q('p'))) if x)

def head_text(body, code):
    for e in body:
        if e.tag == q('p') and style(e) == 'Heading1' and ptext(e).startswith(code):
            return ptext(e)
    return code

def clean(s):
    return LABEL.sub('', s).strip()

class Lit(str): pass
yaml.add_representer(Lit, lambda d, s: d.represent_scalar('tag:yaml.org,2002:str', s, style='|'))
def dump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(obj, f, allow_unicode=True, sort_keys=False, width=1000)

def fm(path, meta, body):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write('---\n' + yaml.dump(meta, allow_unicode=True, sort_keys=False, width=1000) + '---\n' + body.strip() + '\n')

made = []
# ---------------- entities ----------------
SKIP = {'K01', 'K03', 'K05', 'K23', 'K24'}
for n in range(1, 23):
    code = f'K{n:02d}'
    if code in SKIP: continue
    els = section(b3, code)
    title = re.sub(r'^K\d\d\s+K\d\d\s*', '', head_text(b3, code))
    notes, fields, links, entity = [], [], [], ''
    for e in els:
        if e.tag == q('p'):
            t = clean(ptext(e))
            if not t: continue
            m = re.match(r'^([a-z_]+)\.\s+(.*)$', t, re.S)
            if m and not entity:
                entity = m.group(1); notes.append(m.group(2))
            else:
                notes.append(t)
        elif e.tag == q('tbl'):
            rows = e.findall(q('tr'))
            hdr = ctext(rows[0].findall(q('tc'))[0])
            for tr in rows[1:]:
                c = [ctext(tc) for tc in tr.findall(q('tc'))]
                if hdr.startswith('Поле'):
                    first = c[0].split('\n', 1)
                    name = first[0].split(' — ')[0].strip()
                    ttl = first[1] if len(first) > 1 else (first[0].split(' — ', 1)[1] if ' — ' in first[0] else '')
                    fields.append({'name': name, 'title': ttl.replace('\n', ' '), 'type': c[1].replace('\n', '; '), 'key': c[2].replace('\n', ' '), 'source': c[3].replace('\n', ' ')})
                elif hdr.startswith('FK'):
                    links.append({'id': c[0], 'link': c[1], 'required': c[2]})
    obj = {'id': code, 'entity': entity or code.lower(), 'title': title, 'note': Lit('\n'.join(notes)), 'fields': fields}
    if links: obj['links'] = links
    dump(f'{R}/model/{entity or code}.yaml', obj); made.append(code)

# ---------------- R-rules ----------------
for n in range(1, 40):
    code = f'R-{n:03d}'
    els = section(b4, code)
    title = re.sub(r'^R-\d{3}\s+R-\d{3}\s*', '', head_text(b4, code)).strip()
    paras = [clean(ptext(e)) for e in els if e.tag == q('p') and ptext(e)]
    if not paras: continue
    statement = paras[0]
    body = []
    for p in paras[1:]:
        m = re.match(r'^([А-ЯЁA-Z][^:]{2,40}):\s*(.*)$', p, re.S)
        body.append(f'**{m.group(1)}.** {m.group(2)}' if m else p)
    fm(f'{R}/rules/{code}.md', {'id': code, 'title': title or statement[:70], 'summary': statement, 'origin': 'КЭ1-04 § ' + code}, statement + '\n\n' + '\n\n'.join(body))
    made.append(code)

def table_rows(sec):
    for e in section(b4, sec):
        if e.tag == q('tbl'):
            for tr in e.findall(q('tr'))[1:]:
                yield [ctext(tc) for tc in tr.findall(q('tc'))]

# invariants
for c in table_rows('INVARIANTS'):
    code = c[0].strip(); text = c[1]
    fm(f'{R}/rules/{code}.md', {'id': code, 'title': 'Инвариант ' + code, 'summary': text, 'origin': 'КЭ1-04 § INVARIANTS', 'kind_note': 'инвариант'},
       f'{text}\n\n**Источник.** {c[2]}'); made.append(code)
# atomic boundaries
for c in table_rows('ATOMIC'):
    m = re.match(r'^(T\d)\s+(.*)$', c[0]); code, ttl = m.group(1), m.group(2)
    fm(f'{R}/rules/{code}.md', {'id': code, 'title': 'Граница фиксации: ' + ttl, 'summary': f'В одной локальной транзакции: {c[1]}.', 'origin': 'КЭ1-04 § ATOMIC'},
       f'**Внутри одной транзакции.** {c[1]}\n\n**За пределами.** {c[2]}'); made.append(code)
# constraints
cur = None; cons = {}
for e in section(b4, 'CONSTRAINTS'):
    if e.tag != q('p'): continue
    t = ptext(e)
    t2 = clean(t) if t.startswith('1.4') else t
    m = re.match(r'^(C\d\d)(?: / MC\d\d)?\.\s*(.*)$', t2, re.S)
    if m:
        cur = m.group(1); cons[cur] = [m.group(2) + (' (профиль РЦД)' if t.startswith('1.4') else '')]
    elif cur and t.startswith('1.4'):
        cons[cur].append('**Профиль РЦД.** ' + clean(t))
for code, parts in cons.items():
    fm(f'{R}/rules/{code}.md', {'id': code, 'title': 'Ограничение ' + code, 'summary': parts[0].split('. ')[0] + '.', 'origin': 'КЭ1-04 § CONSTRAINTS'}, '\n\n'.join(parts))
    made.append(code)
# states
rows = list(table_rows('STATES'))
body = 'Коды — словарь CD-D-11; области кодов разных объектов раздельны.\n\n'
for c in rows:
    if len(c) < 3: continue
    obj = c[0].split(' ')[0]
    body += f'## {c[0]} {{#{obj}}}\n\n**Переходы.** `{c[1]}`\n\n{c[2]}\n\n'
fm(f'{R}/rules/STATES.md', {'id': 'STATES', 'title': 'Состояния объектов и переходы', 'summary': 'Отдельная машина состояний у каждого объекта; конечный исход — только по доказательству.', 'origin': 'КЭ1-04 § STATES'}, body)
made.append('STATES')
# REV-R not yet in pilot
have = {os.path.basename(p)[:-3] for p in os.listdir(f'{R}/rules')}
for c in table_rows('Условия применения профилей и счетов'):
    m = re.match(r'^(REV-R\d+)\s+(.*)$', c[0])
    if not m or m.group(1) in have: continue
    code = m.group(1)
    fm(f'{R}/rules/{code}.md', {'id': code, 'title': m.group(2), 'summary': c[1].split('. ')[0] + '.', 'origin': 'КЭ1-04 § REV'}, f'{c[1]}\n\n**Опора.** {c[2]}')
    made.append(code)

# ---------------- dictionaries ----------------
for code in ['CD-D-11', 'CD-D-12', 'CD-D-15', 'CD-D-16', 'CD-D-20', 'CD-D-27']:
    els = section(b3, code)
    title = re.sub(r'^CD-D-\d\d\s+CD-D-\d\d\s*', '', head_text(b3, code))
    notes, fields = [], []
    for e in els:
        if e.tag == q('p'):
            t = clean(ptext(e))
            if t and not t.startswith('Опора полей') and t not in notes: notes.append(t)
        elif e.tag == q('tbl'):
            for tr in e.findall(q('tr'))[1:]:
                c = [ctext(tc) for tc in tr.findall(q('tc'))]
                fields.append({'name': c[0], 'type': c[1]})
    seen = set(); uniq = []
    for n_ in notes:
        k = n_[:80]
        if k in seen: continue
        seen.add(k); uniq.append(n_)
    dump(f'{R}/config/{code}.yaml', {'id': 'CFG-' + code, 'title': title, 'version': 'черновик из КЭ1-03', 'note': Lit('\n\n'.join(uniq)), 'fields': fields})
    made.append(code)
print(len(made), made)
