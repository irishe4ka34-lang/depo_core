"""Перенос остатка томов 01–06 «как есть» по идентификаторам, с пометками предварительного ревью.
Вход: /home/claude/work/sec (разрезка актуальных docx по заголовкам 1-го уровня)."""
import os, re, json, yaml
SEC = '/home/claude/work/sec'
R = os.path.join(os.path.dirname(__file__), '..', 'repo')
IDX = json.load(open(f'{SEC}/index.json'))
SRC = {(v, c): f for v, c, n, f in IDX}
VOL = {'01': 'КЭ1-01 Границы', '02': 'КЭ1-02 Сценарии', '03': 'КЭ1-03 Модель и справочники', '04': 'КЭ1-04 Правила', '05': 'КЭ1-05 Архитектура', '06': 'КЭ1-06 Приёмка'}
AS_IS = 'перенесено как есть'

def body_of(path):
    lines = open(path, encoding='utf-8').read().split('\n')[1:]
    out, in_tbl, seen = [], False, set()
    for ln in lines:
        if ln.startswith('|'):
            if not in_tbl:
                out.append('')
                out.append(ln)
                out.append('|' + '---|' * (ln.count('|') - 1))
                in_tbl = True
            else:
                out.append(ln)
            continue
        if in_tbl:
            out.append(''); in_tbl = False
        key = re.sub(r'^Содержание исходного каталога:\s*', '', ln)[:80]
        if len(ln) > 60 and key in seen:   # повтор абзаца из сборки 1.4
            continue
        seen.add(key)
        out.append(ln if ln.startswith('## ') else ln)
        out.append('')
    s = '\n'.join(out)
    return re.sub(r'\n{3,}', '\n\n', s).strip()

def summary_of(body):
    for p in body.split('\n\n'):
        p = p.strip()
        if p and not p.startswith(('|', '#', '1.4 ·')):
            p = re.sub(r'^(В Э1|После Э1)\.\s*', '', p)
            s = re.split(r'(?<=[.;])\s', p, maxsplit=1)[0]
            return s[:260]
    return ''

def auto_review(text, kind):
    notes = []
    if re.search(r'\bOD-1[13]\b|UC027-Q3', text):
        notes.append('Ссылается на закрытые вопросы OD-11/OD-13/UC027-Q3 — виды счетов и разделы решены (DEC-2026-10-21-01, -02, REV-R20), параметры выпуска — DEC-2026-10-21-04.')
    if re.search(r'is_test|синтетич', text):
        notes.append('Остатки пробного этапа (is_test, «синтетические» данные) — для продукта убрать; в тестовых фикстурах допустимо.')
    if re.search(r'ExactDecimal|[Тт]очное decimal', text):
        notes.append('Количество описано как decimal — по решению REV-R12 это целое число минимальных единиц с масштабом выпуска.')
    if kind == 'uc' and re.search(r'^В Э1\.|^После Э1\.', text, re.M):
        notes.append('Рамка «В Э1 / После Э1» — от пробного этапа. По новой рамке: что действует в ядре сейчас, что включается настройкой CD-D-10, что вне ядра.')
    n = len(re.findall(r'Опора|SRC-\d|RV2-|E1C?-\d|P\d{5}', text))
    if n >= 15:
        notes.append(f'Много ссылок на исходный каталог пакета ({n}) — при ревью перенести в origin, в тексте оставить нормы и правила.')
    return notes

MANUAL = {
 'SCOPE': ['Противоречие внутри раздела: новая рамка (ядро промышленного назначения без данных, с настройками) и прежняя фраза «реальные клиент, права, выплаты и промышленная ОИС не входят в Э1». Вторую фразу нужно убрать или переформулировать: в Э1 нет интеграции и выплат, но учёт — реальный.'],
 'TYPES': ['Строка «Количество права — точное decimal» противоречит строке «Количество: представление и точность» того же раздела (целые минимальные единицы, REV-R12). Оставить вторую.'],
 'DICTIONARIES': ['Общее поле справочника is_test — убрать: справочник ядра не делится на тестовый и боевой.'],
 'D-GAPS': ['DICT-F01: «21 сущность, 201 атрибут» — устарело, сейчас 24 сущности (K22–K24 добавлены).'],
 'SOURCE-MAP': ['Метаописание пакета (как проверялось покрытие исходного каталога). Для разработки не нужно — кандидат в архив.'],
 'BOUNDARY': ['В основном трассировка к исходному каталогу UC-001–074 — кандидат в архив; полезна только таблица «что в ядре, что во внешнем компоненте».'],
 'LOGICAL': ['Трассировка к исходному каталогу — кандидат в архив после сверки с моделью K01–K24.'],
 'DEFERRED-D': ['Справочники будущих этапов: часть уже нужна сейчас — календарь операционного дня (892-П п.1.3–1.4) и учёт выплат (п.1.10, вопрос RV-03).'],
 'UC-066': ['892-П п.1.3–1.4 закрывает часть вопроса OD-14: операционный день единый, оканчивается не позднее 12:00 МСК ближайшего рабочего дня; после окончания операции за этот день не совершаются.'],
 'UC-067': ['Закрытие операционного дня нужно основной цепочке: от него зависят выписка на дату (п.14.1) и окно исправления ошибок (п.1.6, RV-01). Кандидат в основную цепочку.', '892-П п.1.3–1.4 закрывает часть вопроса OD-14 (граница дня).'],
 'UC-041': ['Связан с RV-01: без коррекции MX08 ошибку нельзя исправить в окне п.1.6 (тот же операционный день, до отчёта).'],
 'UC-049': ['Закрытие дела после ревью разрешено по R-009 (повторная сверка + второй сотрудник); текст «закрытие отложено» устарел.'],
 'UC-048': ['Акт о расхождениях в день сверки и уведомление Банка России — R-026; в сценарии расследования это не упомянуто.'],
 'FORM-029': ['Группа «Вид и режим — утверждённый справочник OD-13» устарела: виды — CD-D-08 с флагами (DEC-2026-10-21-01), посредники — REV-R17–R22, полномочие — K24.'],
 'STATE-UC-032': ['Устарело после DEC-2026-10-22-01: переходы заявления теперь DRAFT → PREPARED → PENDING → CONFIRMED/REJECTED/UNKNOWN; актуальная таблица — в UC-032.'],
 'IF-01': ['Канал, состав заявления и ответа, доказательство открытия и отказ от контролёра решены DEC-2026-10-22-01 — текст IF-01 сверить с UC-032.'],
 'FORM-032': ['Форму сверить с UC-032 после DEC-2026-10-22-01: черновик, регистрация передачи с комплектом, уведомление оператора, без контролёра.'],
 'STATE-UC-033': ['Устарело после DEC-2026-10-22-02: шаг получения выписки ОИС, автоматическая готовность при совпадении, остаток без основания — на XY (REV-R27); актуальная таблица — в UC-033.'],
 'STATE-UC-029': ['А3 «Ожидает решения OD-13» устарела — OD-13 закрыт.'],
 'IF-05': ['Процесс на стороне ОИС (проверка допуска ЦД); в ЦД — только хранение подтверждения. Кандидат «вне ядра».'],
 'IF-06': ['Жизненный цикл счёта N у ОИС; закрытие и приостановление счёта N должны вести к статусам AA (вопрос RV-06).'],
 'ARCH': ['Слова «прототип», «пробный» отсутствуют, но «ручной обмен в Э1» и «целевая декомпозиция» согласуются с новой рамкой — проверить формулировку про ЭП в UC-027.'],
 'V11-FIX-01': ['Содержание уже вошло в R-004 и I05 — кандидат в архив.'],
 'V11-FIX-02': ['Содержание вошло в R-009; срок «один рабочий день» — требование БТ, норма 892-П не найдена.'],
 'V11-FIX-03': ['Содержание вошло в R-009.'],
 'V11-FIX-04': ['Содержание вошло в R-008.'],
 'CD-D-13': ['quantity: ExactDecimal → целое число минимальных единиц (REV-R12). Сущности экземпляра ограничения нет (MODEL-Q11).'],
 'CD-D-24': ['Связан с UC-069 и OD-14; операционный день из п.1.3–1.4 892-П — в CD-D-15.'],
 'CD-D-28': ['Числовые показатели не заданы (BR-NFR-03/08) — ждут владельца бизнеса.'],
}

def write_md(folder, id_, title, body, origin, kind, status=AS_IS, extra=None):
    os.makedirs(f'{R}/{folder}', exist_ok=True)
    meta = {'id': id_, 'title': title, 'summary': summary_of(body), 'status': status, 'origin': origin}
    rv = MANUAL.get(id_, []) + auto_review(body, kind)
    if rv: meta['review'] = rv
    if extra: meta.update(extra)
    with open(f'{R}/{folder}/{id_}.md', 'w', encoding='utf-8') as f:
        f.write('---\n' + yaml.dump(meta, allow_unicode=True, sort_keys=False, width=1000) + '---\n' + body + '\n')
    return id_

made = []
NAMES = {  # безымянные разделы → идентификаторы
 'Нормативные основания и решения для ревью': 'NORMS-REVIEW', 'Уточнения редакции 1 3 и происхождение вопросов': 'ORIGIN-13',
 'Применение профилей в сценариях': 'PROFILES-UC', 'Четыре профиля цифровых прав для ревью': 'PROFILES',
 'Условная матрица операций CD D 10': 'MATRIX-NOTE', 'Схема учётных счетов и внешних связей': 'ACC-SCHEME',
 'Границы интерфейсов для профилей ЦФА': 'IF-PROFILES', 'Проверки дополнения для ревью': 'AC-REVIEW',
}
CHAIN = {'UC-027', 'UC-029', 'UC-032', 'UC-033', 'UC-037', 'UC-046', 'UC-047', 'UC-056', 'UC-057'}
SKIP = re.compile(r'^(K\d\d |R-0\d\d |CD-D-(05|08|09|10|11|12|15|16|20|27) |INVARIANTS|ATOMIC|CONSTRAINTS|STATES|Условия применения профилей|MODEL-Q |ARCH-Q |UC-OPEN|NAV )')
ac06 = {}
for v, c, n, f in IDX:
    m = re.match(r'^(UC-0\d\d)', c)
    if v == '06' and m: ac06[m.group(1)] = f

for v, c, n, f in IDX:
    if SKIP.match(c): continue
    m = re.match(r'^(UC-0\d\d)\s+(.*)$', c)
    if m and v == '02':
        uid, ttl = m.group(1), m.group(2)
        if uid in CHAIN: continue
        body = body_of(f)
        if uid in ac06:
            body += '\n\n## Проверки приёмки (КЭ1-06)\n\n' + body_of(ac06[uid])
        made.append(write_md('usecases', uid, ttl, body, f'КЭ1-02 § {uid}; КЭ1-06 § {uid}', 'uc',
                             status='вне основной цепочки; ' + AS_IS))
        continue
    if v == '06' and m: continue
    m = re.match(r'^(CD-D-\d\d)\s+CD-D-\d\d\s+(.*)$', c)
    if m:   # справочник
        code, ttl = m.groups()
        txt = open(f, encoding='utf-8').read().split('\n')[1:]
        fields, notes = [], []
        for ln in txt:
            if ln.startswith('|'):
                cells = [x.strip() for x in ln.strip('|').split('|')]
                if cells[0] in ('Поле', 'Общее поле'): continue
                fields.append({'name': cells[0], 'type': cells[1] if len(cells) > 1 else ''})
            elif ln.strip():
                k = re.sub(r'^Содержание исходного каталога:\s*', '', ln)[:80]
                if any(x[:80] == k for x in notes): continue
                notes.append(ln.strip())
        rv = MANUAL.get(code, []) + auto_review('\n'.join(txt), 'cfg')
        obj = {'id': 'CFG-' + code, 'title': ttl, 'version': AS_IS, 'note': '\n\n'.join(notes), 'origin': f'КЭ1-03 § {code}'}
        if rv: obj['review'] = rv
        obj['fields'] = fields
        yaml.dump(obj, open(f'{R}/config/{code}.yaml', 'w', encoding='utf-8'), allow_unicode=True, sort_keys=False, width=1000)
        made.append(code); continue
    m = re.match(r'^((?:STATE-UC-0\d\d|V11-FIX-0\d|IF-0\d|IF-COMMON|FORM-0\d\d|BR-NFR-\d\d|NFR-GATE|UI-CROSS|[A-Z][A-Z-]+))\s+(.*)$', c)
    if m:
        id_, ttl = m.groups()
        ttl = re.sub(r'^' + re.escape(id_) + r'\s+', '', ttl)
    else:
        id_, ttl = NAMES[c], c
    body = body_of(f)
    if v == '05':
        folder, kind = 'arch', 'arch'
    elif id_.startswith('V11-FIX'):
        folder, kind = 'rules', 'rule'
    else:
        folder, kind = 'guide', 'guide'
    made.append(write_md(folder, id_, ttl, body, f'{VOL[v]} § {c.split()[0] if m else c}', kind))

# --- вопросы ARCH-Q и недостающие MODEL-Q
def rows(name):
    for ln in open(SRC[('01', name)], encoding='utf-8').read().split('\n'):
        if ln.startswith('|'):
            yield [x.strip() for x in ln.strip('|').split('|')]
ARQ_NOTE = {
 'ARCH-Q12': 'Частично отвечено 892-П п.4.2: статусы счёта — открыт, приостановлен, возобновлён, закрыт (STATES#account, RV-05).',
 'ARCH-Q13': 'Для зачисления отвечено C01 и 892-П п.8.6 (двойная запись); для остальных операций — по мере включения в CD-D-10.',
 'ARCH-Q20': 'Частично отвечено 892-П п.1.3–1.4: операционный день оканчивается не позднее 12:00 МСК ближайшего рабочего дня; после окончания операции за день не совершаются.',
 'ARCH-Q24': 'Вопрос к документам ОИС (БТ/SM), а не к ЦД — передать в проект ОИС или закрыть.',
 'ARCH-Q25': 'Вопрос к документам ОИС (контракт кошелька) — передать в проект ОИС или закрыть.',
 'ARCH-Q26': 'Вопрос к документам ОИС — передать в проект ОИС или закрыть.',
 'ARCH-Q27': 'Вопрос к документам ОИС — передать в проект ОИС или закрыть.',
 'ARCH-Q28': 'Вопрос к документам ОИС; источник AA — 892-П гл.10 (RV-06).',
 'ARCH-Q29': 'Вопрос к документам ОИС — передать в проект ОИС или закрыть.',
}
def q_md(qid, title, question, until='', note=''):
    meta = {'id': qid, 'title': title, 'summary': question[:300], 'status': 'открыт', 'origin': 'КЭ1-01 § ' + qid.split('-')[0] + '-Q'}
    if note: meta['review'] = [note]
    body = f'**Вопрос.** {question}' + (f'\n\n**До решения.** {until}' if until else '')
    with open(f'{R}/questions/{qid}.md', 'w', encoding='utf-8') as f:
        f.write('---\n' + yaml.dump(meta, allow_unicode=True, sort_keys=False, width=1000) + '---\n' + body + '\n')
    made.append(qid)
for c in rows('ARCH-Q  Архитектурные вопросы'):
    if not c[0].startswith('ARCH-Q'): continue
    title = re.sub(r'\?$', '', c[1])[:70]
    q_md(c[0], title, c[1], note=ARQ_NOTE.get(c[0], ''))
for c in rows('MODEL-Q  Вопросы модели Q01–Q11'):
    mm = re.match(r'^(MODEL-Q\d\d)', c[0])
    if not mm or os.path.exists(f'{R}/questions/{mm.group(1)}.md'): continue
    q_md(mm.group(1), c[1][:70], c[1], c[2] if len(c) > 2 else '')
# раздел UC-OPEN и DECISIONS — как справка
for name, id_ in [('UC-OPEN  Незакрытые решения по сценариям', 'UC-OPEN')]:
    made.append(write_md('guide', id_, 'Незакрытые решения по сценариям', body_of(SRC[('01', name)]), 'КЭ1-01 § UC-OPEN', 'guide'))
print(len(made)); print(' '.join(made))
