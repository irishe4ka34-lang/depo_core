"""Сборка развёрнутого представления сценария из источников docs-as-code.
Источники: repo/norms, rules, decisions (*.md с YAML front matter), model, config (*.yaml),
usecases (*.md), acceptance (*.feature). Ссылки в тексте: [[ID]] или [[ID#якорь]]."""
import re, json, glob, os, html, sys
import yaml, markdown

ROOT = os.path.join(os.path.dirname(__file__), 'repo')
REF = re.compile(r'\[\[([A-Za-z0-9\-]+)(?:#([A-Za-z0-9.\-]+))?(?:~([^\]]+))?\]\]')
AUTO_STATS = {}
KIND = {'norms': 'Норма', 'rules': 'Правило', 'decisions': 'Решение', 'model': 'Модель', 'config': 'Настройка', 'usecases': 'Сценарий', 'questions': 'Вопрос', 'arch': 'Архитектура', 'guide': 'Справка'}
errors = []

def md(text):
    return markdown.markdown(text, extensions=['tables', 'attr_list', 'md_in_html'])

def front(path):
    s = open(path, encoding='utf-8').read()
    m = re.match(r'^---\n(.*?)\n---\n(.*)$', s, re.S)
    return yaml.safe_load(m.group(1)), m.group(2)

REG = {}   # id -> {kind,title,summary,html,sections{anchor:{title,html}},file,sources}
for folder in ['norms', 'rules', 'decisions', 'usecases', 'questions', 'arch', 'guide']:
    for f in sorted(glob.glob(f'{ROOT}/{folder}/*.md')):
        meta, body = front(f)
        sections = {}
        parts = re.split(r'^(## .*)$', body, flags=re.M)
        for i in range(1, len(parts), 2):
            h = parts[i]; m = re.search(r'\{#([^}]+)\}', h)
            if m:
                title = re.sub(r'\s*\{#[^}]+\}', '', h[3:]).strip()
                sections[m.group(1)] = {'title': title, 'md': parts[i + 1].strip()}
        REG[meta['id']] = dict(kind=KIND[folder], title=meta['title'], summary=meta.get('summary', ''),
                               md=re.sub(r'\s*\{#[^}]+\}', '', body), sections=sections,
                               file=os.path.relpath(f, ROOT), sources=meta.get('sources', []),
                               meta={k: v for k, v in meta.items() if k in ('source', 'checked', 'status', 'owner', 'date', 'decision', 'config', 'review', 'origin')},
                               applies_to=meta.get('applies_to', []), fm=meta)

HDR = {'title': 'Смысл', 'key': 'Ключ и область', 'source': 'Источник и проверка', 'id': 'ID', 'link': 'Связь', 'code': 'Код', 'operation': 'Операция', 'accounts': 'Счета', 'basis': 'Основание', 'extra_checks': 'Проверки сверх G', 'enabled_e1': 'В Э1',
       'legal_kind': 'Вид по закону', 'name': 'Название', 'codes': 'Коды 892-П', 'release_enabled': 'Включён', 'until': 'До решения', 'blocked_by': 'Блокирует',
       'condition': 'Условие', 'when': 'Когда', 'profile': 'Профиль', 'require': 'Обязательные поля', 'type': 'Тип', 'required': 'Обязательность', 'trace': 'Основание', 'note': 'Примечание'}
def cell(v):
    if v is True: return 'Да'
    if v is False: return 'Нет'
    return '' if v is None else str(v).replace('|', '/')
def yaml_table(rows, cols):
    head = '| ' + ' | '.join(HDR.get(c, c) for c in cols) + ' |\n|' + '---|' * len(cols) + '\n'
    return head + ''.join('| ' + ' | '.join((f'[[{r[c]}]]' if c == 'trace' and re.match(r'^[A-Z][A-Z0-9-]+\d(#[\w.]+)?$', str(r.get(c) or '')) else cell(r.get(c, ''))) for c in cols) + ' |\n' for r in rows)

MODEL_FIELDS = []
for f in sorted(glob.glob(f'{ROOT}/model/*.yaml')):
    y = yaml.safe_load(open(f, encoding='utf-8'))
    for fl in y['fields']:
        MODEL_FIELDS.append((y['id'], y['entity'], fl))
    fcols = ['name', 'title', 'type', 'required', 'key', 'trace', 'note'] if any('title' in f_ for f_ in y['fields']) else ['name', 'type', 'required', 'trace', 'note']
    mdtxt = yaml_table(y['fields'], fcols)
    if y.get('links'):
        mdtxt += '\n\n**Связи.**\n\n' + yaml_table(y['links'], ['id', 'link', 'required'])
    REG[y['id']] = dict(kind='Модель', title=f"{y['id']} {y['title']} ({y['entity']})", summary=(y.get('note', '') or '')[:600],
                        md=mdtxt, sections={},
                        file=os.path.relpath(f, ROOT), sources=[], meta={})
for f in sorted(glob.glob(f'{ROOT}/config/*.yaml')):
    y = yaml.safe_load(open(f, encoding='utf-8'))
    rows = y.get('kinds') or y.get('cases') or y.get('rules') or y.get('operations') or y.get('fields')
    cols = (['legal_kind', 'name', 'codes', 'release_enabled', 'until', 'blocked_by', 'condition'] if 'kinds' in y
            else ['profile', 'when', 'require'] if 'rules' in y
            else ['code', 'operation', 'PF1', 'PF2', 'PF3', 'PF4', 'accounts', 'basis', 'extra_checks', 'enabled_e1'] if 'operations' in y
            else ['name', 'type', 'note'] if 'fields' in y
            else ['code', 'when'])
    for r in rows:
        if isinstance(r.get('codes'), list): r['codes'] = ', '.join(r['codes']) or '—'
    REG[y['id']] = dict(kind='Настройка', title=f"{y['id']} {y['title']}", summary=(y.get('note', '') + ' ' if y.get('note') else '') + f"Версия {y['version']}; файл загружается в ядро как есть.",
                        md=yaml_table(rows, cols), sections={}, file=os.path.relpath(f, ROOT), sources=[], meta={'version': y['version'], 'review': y.get('review'), 'origin': y.get('origin')})

def parse_feature(path):
    out = []
    feat = open(path, encoding='utf-8').read()
    for b in re.split(r'\n(?=  @)', feat)[1:]:
        lines = b.strip('\n').split('\n')
        tags = lines[0].split()
        out.append({'tags': [t[1:] for t in tags], 'title': lines[1].strip(),
                    'text': '\n'.join(l[2:] if l.startswith('  ') else l for l in lines[1:]).rstrip()})
    return out

def check(ref, anc, where):
    if ref not in REG and not ref.startswith(('UC-0', 'FORM')):
        errors.append(f'{where}: нет {ref}')
    elif anc and ref in REG and anc not in REG[ref]['sections']:
        errors.append(f'{where}: нет якоря {ref}#{anc}')

def refs_to_html(h, where):
    def sub(m):
        ref, anc = m.group(1), m.group(2)
        check(ref, anc, where)
        key = ref + ('#' + anc if anc else '')
        if ref not in REG:
            return f'<span class="ref ext">{html.escape(key)}</span>'
        e = REG[ref]
        if m.group(3):
            return (f'<button class="ref k-{e["kind"]} alias" data-ref="{html.escape(key)}" aria-expanded="false">'
                    f'<span class="rid">{html.escape(m.group(3))}</span></button>')
        label = re.sub(r'^\d+\.\d+(?:[–-]\d+\.\d+)?\s+', '', e['sections'][anc]['title']) if anc and anc in e['sections'] else e['title'].split('—')[-1].strip()
        short = ref + (' п.' + anc if anc and re.match(r'^\d', anc) else '')
        return (f'<button class="ref k-{e["kind"]}" data-ref="{html.escape(key)}" aria-expanded="false">'
                f'<span class="rid">{html.escape(short)}</span><span class="rl">{html.escape(label)}</span></button>')
    return REF.sub(sub, h)


def norm_anchor(xy):
    for rid, e in REG.items():
        if rid.startswith('NR-892-') and xy in e['sections']:
            return rid + '#' + xy
    return None

AUTO = [
    (re.compile(r'КЭ1-0\d\s*§\s*([A-Z][A-Z0-9-]*[A-Z0-9])'), lambda m: m.group(1) if m.group(1) in REG else None),
    (re.compile(r'\b(?:STATE-UC-0\d\d|IF-0\d|IF-COMMON|FORM-0\d\d|BR-NFR-\d\d|ARCH-Q\d\d|V11-FIX-0\d)\b'), lambda m: m.group(0) if m.group(0) in REG else None),
    (re.compile(r'уникальн\w* идентификатор\w* по 892-П'), lambda m: 'NR-892-3#3.10'),
    (re.compile(r'892-П\s+гл\.\s?(\d+)'), lambda m: ('NR-892-' + m.group(1)) if ('NR-892-' + m.group(1)) in REG else None),
    (re.compile(r'(?<![\w.])(?:892-П\s+)?пп?\.\s?(\d+\.\d+)(?:[–-]\d+\.\d+)?'), lambda m: norm_anchor(m.group(1))),
    (re.compile(r'\bPF[1-4](?:\s?[–-]\s?PF[1-4])?\b'), lambda m: 'CFG-CD-D-09'),
    (re.compile(r'\bMX\d{2}(?:\s?[–-]\s?MX\d{2})?\b'), lambda m: 'CFG-CD-D-10'),
    (re.compile(r'\bCD-D-(\d\d)\b'), lambda m: ('CFG-CD-D-' + m.group(1)) if ('CFG-CD-D-' + m.group(1)) in REG else None),
    (re.compile(r'\bK(\d\d)\b'), lambda m: m.group(0) if m.group(0) in REG else None),
    (re.compile(r'\bR-0\d\d\b'), lambda m: m.group(0) if m.group(0) in REG else None),
    (re.compile(r'(?<![\w-])I(0[1-9]|1[0-5])\b'), lambda m: m.group(0) if m.group(0) in REG else None),
    (re.compile(r'(?<![\w-])C(0[1-9]|1[01])\b'), lambda m: m.group(0) if m.group(0) in REG else None),
    (re.compile(r'(?<![\w-])T[1-6]\b(?!-)'), lambda m: m.group(0) if m.group(0) in REG else None),
    (re.compile(r'\bREV-R\d+\b'), lambda m: m.group(0) if m.group(0) in REG else None),
    (re.compile(r'\bUC-0\d\d\b'), lambda m: m.group(0) if m.group(0) in REG else None),
    (re.compile(r'(?:CD:)?\bOD-(\d\d)\b'), lambda m: ('OD-' + m.group(1)) if ('OD-' + m.group(1)) in REG else None),
    (re.compile(r'\b(?:MODEL-Q\d\d|UC0\d\d-Q\d|RCD-D\d|ACC-Q\d|REV-Q\d|RV-\d\d)\b'), lambda m: m.group(0) if m.group(0) in REG else None),
]
PROTECT = re.compile(r'(\[\[[^\]]*\]\]|`[^`]*`|\{[^}]*\})')

INC = re.compile(r'^!include ([A-Z0-9-]+)\s*$', re.M)
def expand(text):
    def sub(m):
        if m.group(1) not in REG:
            errors.append(f'include: нет {m.group(1)}'); return ''
        return REG[m.group(1)]['md']
    return INC.sub(sub, text)

def autolink(text, self_id):
    text = expand(text)
    out_lines = []
    for line in text.split('\n'):
        if line.startswith('#') or line.startswith('---') or line.lstrip().startswith('<'):
            out_lines.append(line); continue
        parts = PROTECT.split(line)
        for i in range(0, len(parts), 2):
            seg = parts[i]
            spans = []
            for rx, fn in AUTO:
                for m in rx.finditer(seg):
                    if any(not (m.end() <= a or m.start() >= b) for a, b, _ in spans): continue
                    if self_id in ('PROTOCOL', 'CHAIN') and rx.pattern.startswith('(?<![\\w-])T'): continue
                    tgt = fn(m)
                    if not tgt or tgt.split('#')[0] == self_id: continue
                    spans.append((m.start(), m.end(), tgt))
            for a, b, tgt in sorted(spans, reverse=True):
                seg = seg[:a] + f'[[{tgt}~{seg[a:b]}]]' + seg[b:]
                AUTO_STATS[self_id] = AUTO_STATS.get(self_id, 0) + 1
            parts[i] = seg
        out_lines.append(''.join(parts))
    return '\n'.join(out_lines)

PAY = {}
def body_wo_summary(e):
    b = e['md'].lstrip()
    first = b.split('\n\n', 1)
    if e['summary'] and len(first) == 2 and first[0][:40] == e['summary'][:40] and '[[' not in first[0]:
        return first[1]
    return b
for rid, e in REG.items():
    PAY[rid] = dict(kind=e['kind'], title=e['title'], summary=e['summary'], html=refs_to_html(md(autolink(body_wo_summary(e), rid)), rid), file=e['file'], meta=e['meta'])
    for anc, s_ in e['sections'].items():
        PAY[rid + '#' + anc] = dict(kind=e['kind'], title=f"{e['title']} — {s_['title']}", summary='', html=refs_to_html(md(autolink(s_['md'], rid)), rid + '#' + anc), file=e['file'], meta=e['meta'])
for f in glob.glob(f'{ROOT}/acceptance/*.feature'):
    for s_ in parse_feature(f):
        for t in s_['tags']:
            r, _, a = t.partition('#'); check(r, a or None, os.path.basename(f))

def all_refs(text):
    return {(m.group(1) + ('#' + m.group(2) if m.group(2) else '')) for m in REF.finditer(text)}

def closure(keys):
    seen = set(keys); stack = list(keys)
    while stack:
        k = stack.pop(); base = k.split('#')[0]
        if base in REG and REG[base]['kind'] == 'Правило':
            for r in all_refs(REG[base]['md']) | set(REG[base]['sources']):
                if r not in seen: seen.add(r); stack.append(r)
    return seen

UCS = {}
for f in sorted(glob.glob(f'{ROOT}/usecases/*.md')):
    uid = os.path.basename(f)[:-3]; uc = REG[uid]
    if not os.path.exists(f'{ROOT}/acceptance/{uid}.feature'): continue
    scen = parse_feature(f'{ROOT}/acceptance/{uid}.feature')
    uc_steps = {}
    for m in re.finditer(r'^### (Шаг \d)[^\n]*\n(.*?)(?=^### |^## |\Z)', uc['md'], re.M | re.S):
        for r in all_refs(m.group(2)): uc_steps.setdefault(r, []).append(m.group(1))
    for m in re.finditer(r'^- \*\*([АИ]\d)[^*]*\*\*(.*)$', uc['md'], re.M):
        for r in all_refs(m.group(2)): uc_steps.setdefault(r, []).append(m.group(1))
    reach = closure(all_refs(uc['md']))
    trace = []
    for nk in sorted(k for k in PAY if k.startswith('NR-') and (k in reach or k.split('#')[0] in reach)):
        rules = sorted(r for r, e in REG.items() if e['kind'] == 'Правило' and r in reach and (nk in e['sources'] or nk in all_refs(e['md'])))
        fields = [f"{ent}.{fl['name']}" for _, ent, fl in MODEL_FIELDS if fl.get('trace') == nk]
        steps = list(uc_steps.get(nk, []))
        for r in rules: steps += [x for x in uc_steps.get(r, []) if x not in steps]
        tests = [x['title'].split(': ', 1)[-1] for x in scen if nk in x['tags'] or any(r in x['tags'] for r in rules)]
        if rules or steps or tests:
            trace.append({'norm': nk, 'title': PAY[nk]['title'], 'rules': rules, 'fields': fields, 'steps': sorted(set(steps)), 'tests': tests})
    UCS[uid] = dict(title=uc['title'], summary=uc['summary'], html=refs_to_html(md(autolink(uc['md'], uid)), uid), trace=trace, scen=scen)

QS = [dict(id=k, title=e['title'], summary=e['summary'], status=e['meta'].get('status', ''), owner=e['meta'].get('owner', ''), uc=e['applies_to'])
      for k, e in sorted(REG.items()) if e['kind'] == 'Вопрос']
# ---------------- атлас сценариев ----------------
def html_of(text, where):
    return refs_to_html(md(autolink(text, where)), where)
def plain(text):
    t = REF.sub(lambda m: m.group(3) or m.group(1) + ('#' + m.group(2) if m.group(2) else ''), text)
    return re.sub(r'[*`]', '', t).strip()
LANE_BY_WORD = [('Операционист', 'Операционист ЦД'), ('Контролёр', 'Контролёр ЦД'), ('ОИС', 'ОИС'), ('Клиент', 'Клиент / представитель'),
                ('ЛК', 'ЛК ЦД'), ('Интеграционный', 'Интеграционный сервис ЦД')]
BR = re.compile(r'^- \*\*([АИ])(\d+)(?:,\s*шаги?\s*([\d]+)(?:\s*[–-]\s*(\d+))?)?\.\s*(.*?)\*\*\s*(.*)$')
ATLAS = []
for f in sorted(glob.glob(f'{ROOT}/usecases/*.md')):
    uid = os.path.basename(f)[:-3]; e = REG[uid]; fm = e['fm']; body = e['md']
    main = os.path.exists(f'{ROOT}/acceptance/{uid}.feature')
    secs = {m.group(1).strip(): m.group(2).strip() for m in re.finditer(r'^## ([^\n]+)\n(.*?)(?=^## |\Z)', body, re.M | re.S)}
    steps = []
    for i, m in enumerate(re.finditer(r'^### Шаг (\d+)\. ([^\n]+)\n(.*?)(?=^### |^## |\Z)', body, re.M | re.S)):
        n, ttl, txt = int(m.group(1)), m.group(2).strip(), m.group(3).strip()
        lanes = fm.get('lanes') or []
        lane = lanes[i] if i < len(lanes) else next((v for k, v in LANE_BY_WORD if ttl.startswith(k)), 'Система ЦД')
        ctrl = next(iter(re.findall(r'\[\[((?:R-0|REV-R|C|I|T)[\w-]*)', txt)), '')
        steps.append(dict(n=n, title=plain(ttl), lane=lane, ctrl=ctrl, html=html_of(txt, uid)))
    brs = []
    lines = body.split('\n')
    for i, ln in enumerate(lines):
        m = BR.match(ln)
        if not m: continue
        cont = []
        for nxt in lines[i + 1:]:
            if nxt.startswith(('- **', '## ')) or (nxt and not nxt.startswith((' ', '\t'))): break
            cont.append(nxt)
        kind = 'A' if m.group(1) == 'А' else 'E'
        frm = int(m.group(3)) if m.group(3) else (steps[-1]['n'] if steps else 1)
        to = int(m.group(4)) if m.group(4) else frm
        cond = plain(m.group(5)) or plain(re.split(r'(?<=[.→])\s', m.group(6))[0])
        full = (m.group(6) + '\n' + '\n'.join(cont)).strip()
        brs.append(dict(kind=kind, id=m.group(1) + m.group(2), frm=frm, to=to, cond=cond.rstrip(' →.'), html=html_of(full, uid)))
    in_e1 = re.search(r'^В Э1\.\s*(.*)$', body, re.M); after = re.search(r'^После Э1\.\s*(.*)$', body, re.M)
    ATLAS.append(dict(id=uid[3:], uc=uid, title=e['title'], main=main, status=str(fm.get('status', '')),
                      actor=fm.get('actor', ''), participants=', '.join(fm.get('participants', []) or []),
                      goal=html_of(re.split(r'\n\s*\n', secs.get('Цель', '').strip())[0], uid) if secs.get('Цель') else '',
                      pre=html_of(secs.get('Предусловия', ''), uid) if secs.get('Предусловия') else '',
                      req=sorted(set(re.findall(r'UC-0\d\d', secs.get('Предусловия', ''))) - {uid}),
                      in_e1=html_of(in_e1.group(1), uid) if in_e1 else '', after=html_of(after.group(1), uid) if after else '',
                      steps=steps, br=brs))

CAT = {}
for k, e in sorted(REG.items()):
    CAT.setdefault(e['kind'], []).append(dict(id=k, title=e['title'], status=str(e['meta'].get('status') or e['meta'].get('version') or ''), review=bool(e['meta'].get('review'))))
FILES = sorted(os.path.relpath(p, ROOT) for p in glob.glob(f'{ROOT}/**/*', recursive=True) if os.path.isfile(p))

data = dict(PAY=PAY, UCS=UCS, FILES=FILES, QS=QS, CAT=CAT, ATLAS=ATLAS)
tpl = open(os.path.join(os.path.dirname(__file__), 'page.html'), encoding='utf-8').read()
out = tpl.replace('/*DATA*/', 'const DATA=' + json.dumps(data, ensure_ascii=False, default=str).replace('</', r'<\/') + ';')
os.makedirs(os.path.join(os.path.dirname(__file__), 'site'), exist_ok=True)
open(os.path.join(os.path.dirname(__file__), 'site', 'index.html'), 'w', encoding='utf-8').write(out)
print('entries', len(PAY), {k: (len(v['trace']), len(v['scen'])) for k, v in UCS.items()}, 'files', len(FILES))
print('AUTOLINKS', AUTO_STATS)
print('ERRORS', errors or 'нет')
