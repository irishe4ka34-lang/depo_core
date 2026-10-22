"""Пишет правила из rules_v2.py в repo/rules: ссылки на поля модели, нормы, сценарии, происхождение из пакета."""
import os, re, glob, sys, yaml
sys.path.insert(0, os.path.dirname(__file__))
from rules_v2 import R
ROOT = os.path.join(os.path.dirname(__file__), '..', 'repo')
OLD = '/home/claude/pilot_hist/repo_до_чистки/rules'

ENT = {}
for f in glob.glob(f'{ROOT}/model/*.yaml'):
    y = yaml.safe_load(open(f, encoding='utf-8'))
    ENT[y['entity']] = (y['id'], {fl['name'] for fl in y['fields']})
UCTXT = {os.path.basename(f)[:-3]: open(f, encoding='utf-8').read() for f in glob.glob(f'{ROOT}/usecases/*.md')}

errors = []
def field(m):
    e, f = m.group(1), m.group(2)
    if e not in ENT or f not in ENT[e][1]:
        errors.append(f'нет поля {e}.{f}')
        return f'`{e}.{f}`'
    return f'[[{ENT[e][0]}~{e}.{f}]]'

def origin(rid):
    p = f'{OLD}/{rid}.md'
    if not os.path.exists(p): return None, []
    s = open(p, encoding='utf-8').read()
    meta = yaml.safe_load(re.match(r'^---\n(.*?)\n---\n', s, re.S).group(1))
    parts = [meta.get('origin', '')]
    m = re.search(r'RV2-07:P\d+', s); parts += [m.group(0)] if m else []
    m = re.search(r'Основание: ([^.]+)\.', s); parts += [m.group(1).strip()] if m else []
    m = re.search(r'Процессы: ([^.]+)\.', s); parts += ['процессы ' + m.group(1).strip()] if m else []
    m = re.search(r'Опора\.\*\*\s*(.+)', s); parts += ['опора пакета: ' + m.group(1).strip()] if m and not rid.startswith('R-') else []
    m = re.search(r'Источник\.\*\*\s*(E1-[^\n]+|Дополнение[^\n]+|Предложение[^\n]+)', s); parts += ['источник пакета: ' + m.group(1).strip()] if m else []
    ucs = re.findall(r'UC-0\d\d', (re.search(r'Сценарии ЦД: ([^\n]+)', s) or re.search('x^', '')).group(1)) if re.search(r'Сценарии ЦД: ', s) else []
    return '; '.join(p for p in parts if p), ucs

for rid, d in R.items():
    body = re.sub(r'\{\{([a-z_]+)\.([a-z_]+)\}\}', field, d['b'])
    org, legacy_ucs = origin(rid)
    direct = sorted(u for u, t in UCTXT.items() if re.search(rf'(?<![\w-]){re.escape(rid)}(?![\w-])', t))
    applies = sorted(set(direct) | (set(legacy_ucs) & set(UCTXT)))
    meta = {'id': rid, 'title': d['t'], 'summary': d['s'], 'status': d['st']}
    if d['src']: meta['sources'] = d['src']
    if applies: meta['applies_to'] = applies
    if org: meta['origin'] = org
    with open(f'{ROOT}/rules/{rid}.md', 'w', encoding='utf-8') as f:
        f.write('---\n' + yaml.dump(meta, allow_unicode=True, sort_keys=False, width=1000) + '---\n' + body + '\n')
print(len(R), 'правил;', 'ошибки полей:', errors or 'нет')
