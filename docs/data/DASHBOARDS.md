# Metabase Dashboard - LuisBank Data

Sugestão de dashboard

1) KPIs Diários
- Fonte: fact_daily_kpis
- Campos: tx_date, total_transactions, total_amount

2) Ticket Médio por Operação
- Fonte: fact_transactions
- Campos: operation_type, avg(amount)

3) Top Clientes por Saldo
- Fonte: dim_account (sum(balance) por user_id)

4) Segmentação
- Fonte: customer_segments
- Campos: segment, count(user_id)

5) Qualidade de Dados
- Fonte: dw.dq_checks
- Últimos checks (status pass/fail)
- Eventos CDC
  - Fonte: dw.cdc_events

Importação via script
- METABASE_URL=http://localhost:3001
- METABASE_USER=admin
- METABASE_PASSWORD=admin
- METABASE_DB=warehouse
- python scripts/metabase_import.py

SQL sugerido para KPIs (exemplo)
select * from fact_daily_kpis order by tx_date desc;

SQL sugerido para segmentos
select segment, count(*) from customer_segments group by segment;
