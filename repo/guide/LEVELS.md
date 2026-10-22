---
id: LEVELS
title: "Три уровня учёта: обязательства, активы, внешние"
summary: "Одно и то же количество учитывается трижды: перед депонентами (обязательства), в собственном учёте ЦД на счёте активов AA (активы) и у ОИС на нашем счёте N (внешние); уровни сравниваются, а не складываются."
status: действует
sources: [NR-892-8#8.6, NR-892-6#6.1, NR-892-10#10.2]
---
<div class="tw"><svg viewBox="0 0 840 400" width="100%" style="max-width:840px;font-family:'IBM Plex Sans',system-ui,sans-serif" role="img" aria-label="Схема трёх уровней учёта: обязательства и активы в ЦД, внешние — у ОИС">
<rect x="10" y="10" width="500" height="380" rx="10" style="fill:var(--surface);stroke:var(--line)"/>
<text x="26" y="34" style="fill:var(--muted);font-size:12px;letter-spacing:.06em">НАШ ЦД — СОБСТВЕННЫЙ УЧЁТ</text>
<rect x="530" y="10" width="300" height="380" rx="10" style="fill:var(--surface);stroke:var(--line)"/>
<text x="546" y="34" style="fill:var(--muted);font-size:12px;letter-spacing:.06em">ОИС — ВЫШЕСТОЯЩИЙ ОПЕРАТОР</text>
<rect x="26" y="50" width="220" height="300" rx="8" style="fill:var(--rule-bg);stroke:var(--rule)"/>
<text x="38" y="74" style="fill:var(--rule);font-size:15px;font-weight:600">Обязательства</text>
<text x="38" y="92" style="fill:var(--muted);font-size:12px">пассивные счета депонентов</text>
<rect x="38" y="106" width="196" height="34" rx="5" style="fill:var(--surface);stroke:var(--line)"/><text x="48" y="128" style="fill:var(--fg);font-size:13px">Счёт O · клиент А</text><text x="224" y="128" text-anchor="end" style="fill:var(--fg);font-size:13px;font-weight:600">60</text>
<rect x="38" y="146" width="196" height="34" rx="5" style="fill:var(--surface);stroke:var(--line)"/><text x="48" y="168" style="fill:var(--fg);font-size:13px">Счёт O · клиент Б</text><text x="224" y="168" text-anchor="end" style="fill:var(--fg);font-size:13px;font-weight:600">40</text>
<rect x="38" y="186" width="196" height="34" rx="5" style="fill:var(--surface);stroke:var(--line)"/><text x="48" y="208" style="fill:var(--fg);font-size:13px">Счёт T · управляющий</text><text x="224" y="208" text-anchor="end" style="fill:var(--fg);font-size:13px;font-weight:600">0</text>
<rect x="38" y="226" width="196" height="34" rx="5" style="fill:var(--surface);stroke:var(--line)"/><text x="48" y="248" style="fill:var(--fg);font-size:13px">Счёт N посредника</text><text x="224" y="248" text-anchor="end" style="fill:var(--fg);font-size:13px;font-weight:600">0</text>
<line x1="38" y1="274" x2="234" y2="274" style="stroke:var(--rule)"/>
<text x="48" y="294" style="fill:var(--rule);font-size:14px;font-weight:600">Итого</text>
<text x="224" y="294" text-anchor="end" style="fill:var(--rule);font-size:14px;font-weight:600">100</text>
<text x="38" y="320" style="fill:var(--muted);font-size:12px">записи ACCOUNT (K08)</text>
<text x="38" y="336" style="fill:var(--muted);font-size:12px">позиции по счетам (K09)</text>
<rect x="282" y="130" width="212" height="140" rx="8" style="fill:var(--model-bg);stroke:var(--model)"/>
<text x="294" y="154" style="fill:var(--model);font-size:15px;font-weight:600">Активы</text>
<text x="294" y="172" style="fill:var(--muted);font-size:12px">счёт активов ЦД</text>
<rect x="294" y="186" width="188" height="34" rx="5" style="fill:var(--surface);stroke:var(--line)"/><text x="304" y="208" style="fill:var(--fg);font-size:13px">Счёт AA</text><text x="472" y="208" text-anchor="end" style="fill:var(--fg);font-size:13px;font-weight:600">100</text>
<text x="294" y="242" style="fill:var(--muted);font-size:12px">записи COVERAGE (K08)</text>
<text x="294" y="258" style="fill:var(--muted);font-size:12px">один AA на каждый счёт N</text>
<rect x="550" y="130" width="264" height="140" rx="8" style="fill:var(--norm-bg);stroke:var(--norm)"/>
<text x="562" y="154" style="fill:var(--norm);font-size:15px;font-weight:600">Внешние</text>
<text x="562" y="172" style="fill:var(--muted);font-size:12px">наш счёт N у ОИС</text>
<rect x="562" y="186" width="240" height="34" rx="5" style="fill:var(--surface);stroke:var(--line)"/><text x="572" y="208" style="fill:var(--fg);font-size:13px">Счёт N · ном. держатель</text><text x="792" y="208" text-anchor="end" style="fill:var(--fg);font-size:13px;font-weight:600">100</text>
<text x="562" y="242" style="fill:var(--muted);font-size:12px">срез K12 по документу</text>
<text x="562" y="258" style="fill:var(--muted);font-size:12px">оператора (892-П п.6.1)</text>
<line x1="246" y1="203" x2="282" y2="203" style="stroke:var(--fg);stroke-width:1.5"/>
<circle cx="264" cy="203" r="11" style="fill:var(--surface);stroke:var(--fg)"/><text x="264" y="208" text-anchor="middle" style="fill:var(--fg);font-size:13px;font-weight:600">1</text>
<line x1="494" y1="203" x2="550" y2="203" style="stroke:var(--fg);stroke-width:1.5;stroke-dasharray:5 4"/>
<circle cx="520" cy="203" r="11" style="fill:var(--surface);stroke:var(--fg)"/><text x="520" y="208" text-anchor="middle" style="fill:var(--fg);font-size:13px;font-weight:600">2</text>
<text x="282" y="306" style="fill:var(--fg);font-size:13px;font-weight:600">1 · обязательства = активы</text>
<text x="282" y="324" style="fill:var(--muted);font-size:12px">двойная запись, 892-П п.8.6</text>
<text x="282" y="340" style="fill:var(--muted);font-size:12px">разница → K14 delta_internal</text>
<text x="550" y="306" style="fill:var(--fg);font-size:13px;font-weight:600">2 · активы = внешние</text>
<text x="550" y="324" style="fill:var(--muted);font-size:12px">сверка, 892-П гл.6</text>
<text x="550" y="340" style="fill:var(--muted);font-size:12px">разница → K14 delta_external</text>
<text x="550" y="372" style="fill:var(--muted);font-size:12px">связь AA ↔ счёт N — K04</text>
</svg></div>

| Уровень | Где учитывается | Счета | Чем записывается | Кто меняет |
|---|---|---|---|---|
| **Обязательства** | в ЦД | пассивные: O, T, N посредников-ЦД, служебные | записи ACCOUNT [[K08]], позиции [[K09]] | ЦД — операциями по своим счетам |
| **Активы** | в ЦД | счёт активов AA, по одному на каждый наш счёт N ([[NR-892-10#10.2]]) | записи COVERAGE [[K08]] | ЦД — той же операцией, что и обязательства |
| **Внешние** | у ОИС | наш счёт N номинального держателя | подтверждённый срез [[K12]] по документу оператора | только ОИС; ЦД лишь фиксирует срез |

**Два равенства — две проверки.**

1. **Обязательства = активы.** Внутренний учёт ЦД: каждое зачисление клиенту сопровождается такой же записью на AA ([[C01]]), сумма на активных счетах равна сумме на цифровых ([[NR-892-8#8.6]]). Расхождение — ошибка проводок самого ЦД.
2. **Активы = внешние.** Наш учёт совпадает с реальностью у ОИС. Проверяется сверкой по последнему документу оператора на дату сверки ([[NR-892-6#6.1]], [[R-026]]); при расхождении — акт в день сверки и уведомление Банка России.

**Пример зачисления +10.** Одна операция K07: ACCOUNT +10 на счёт клиента (обязательства 100 → 110) и COVERAGE +10 на AA (активы 100 → 110). Внешние ЦД не меняет: по документу ОИС фиксируется новый срез 110 — и сверка подтверждает равенство.

Уровни сравниваются, а не складываются: это одни и те же 100 единиц, а не 300 ([[I01]], [[R-002]]).
