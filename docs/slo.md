# SLOs Operacionais (Ledger)

## Objetivos (30 dias)
- **Latência p95 (API):** <= 1.0s para `app_request_latency_seconds`.
- **Erro de requisições:** <= 0.5% de respostas 5xx.
- **Falha de transações:** <= 0.1% de transações com erro (4xx/5xx em endpoints críticos).
- **Integridade do ledger:** 100% dos checks com `ledger_integrity_ok == 1`.

## SLIs e PromQL
- **Latência p95**
  - `histogram_quantile(0.95, sum(rate(app_request_latency_seconds_bucket[5m])) by (le))`
- **Erro de requisições (5xx)**
  - `sum(rate(app_errors_total{status=~"5.."}[5m])) / sum(rate(app_request_latency_seconds_count[5m]))`
- **Falha de transações (4xx/5xx nos endpoints de transação)**
  - `sum(rate(app_errors_total{path=~"/ledger/(transactions|transfers|pix/transfer)",status=~"[45].."}[5m])) / sum(rate(app_request_latency_seconds_count{path=~"/ledger/(transactions|transfers|pix/transfer)"}[5m]))`
- **Integridade do ledger**
  - `ledger_integrity_ok`
  - `time() - ledger_integrity_last_run_timestamp`

## Orçamento de erro
- **Latência:** 1% das janelas de 5m acima do p95 alvo.
- **Erro:** 0.5% de erro total em 30 dias.
- **Ledger:** nenhuma falha; qualquer `ledger_integrity_ok == 0` gera alerta crítico.
