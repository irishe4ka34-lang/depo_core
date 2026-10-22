---
id: IDENTIFIERS
title: Различие идентификаторов
summary: ''
status: перенесено как есть
origin: КЭ1-03 Модель и справочники § IDENTIFIERS
---
| Контрактное имя | Поле модели | Различие |
|---|---|---|
| requestId | command_receipt.request_key / external_operation.request_key | Внутренний запрос и ключ запроса ОИС различаются; mapping сохраняется. |
| eventId | external_event.event_id + source_system | Ключ события, не ключ бухгалтерского/экономического эффекта. |
| operationId | external_operation.external_id либо external_event.external_operation_key | ID ОИС. accounting_operation.id — отдельный внутренний ID. |
| entryId | accounting_entry.id | Первичная запись ЦД. |
| accountId | account.id | Внешний accountId хранится в custody_link.external_account_id. |
| statementId | statement.id | Повтор запроса возвращает тот же экземпляр; новый исправленный — новый ID. |
| caseId / runId | discrepancy_case.id / reconciliation_run.id | Дело и запуск сверки не один объект. |
| correlationId | command_receipt/external_event.correlation_id | Для прослеживания; не гарантия уникальности или доказательство полномочия. |
| deponentId / deponentCode | K04.external_depositor_id | Наш ЦД как депонент РЦД; не account_id и не party_ref |
| depoAccountId / depoAccountNo | K04.external_account_id / external_account_no | ID и номер счёта у РЦД хранятся раздельно; accountId и segCode — устаревшие имена тех же полей |
| sectionCode | K04.section_code | Раздел счёта у РЦД; часть custody_key |
| operationId (clientOperationId) | K11.request_key | Наш ключ поручения РЦД; не переиспользуется для нового поручения |
| receiptId (depoOperationId) | K11.external_id | Ключ поручения у РЦД; основа ключа повтора C07 |
| updateNo | K11.last_update_no | Порядок изменения статуса; не ключ; ответ с меньшим номером класс не меняет |
| ticker | K03.ticker | Не глобальный ключ актива; ключ ЦВ — network + symbol |
