# Sugestoes para documentacao no GitHub

1) Arquitetura de dados
- Diagrama: fonte (ledger_db) -> warehouse_db -> dbt -> BI
- Justificativa de schema dimensional

2) Pipeline
- Airflow DAG ledger_etl (descricao das tasks)
- Frequencia, retries e monitoramento

3) Modelagem
- Staging: stg_users, stg_accounts, stg_transactions, stg_postings, stg_kyc_profiles
- Marts: dim_customer, dim_account, fact_transactions, fact_postings, fact_daily_kpis
- Segmentacao: customer_segments

4) Qualidade
- Checks automaticos (dw.dq_checks)
- Politicas de tolerancia

5) Analises prontas
- KPIs diarios
- Ticket medio por tipo
- Saldo medio
- Cohort por data de abertura

6) Reproducibilidade
- Script de geracao fake
- Parametros de seed
- Exports CSV

7) Roadmap
- Incremental load por watermark (ja aplicado)
- Particionamento por mes (ja aplicado)
- CDC via WAL (ja documentado)
- Observabilidade com SLIs/SLOs
