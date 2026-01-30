# Sugestões para documentação no GitHub

1) Arquitetura de dados
- Diagrama: fonte (ledger_db) -> warehouse_db -> dbt -> BI
- Justificativa de schema dimensional

2) Pipeline
- Airflow DAG ledger_etl (descrição das tasks)
- Frequência, retries e monitoramento

3) Modelagem
- Staging: stg_users, stg_accounts, stg_transactions, stg_postings, stg_kyc_profiles
- Marts: dim_customer, dim_account, fact_transactions, fact_postings, fact_daily_kpis
- Segmentação: customer_segments

4) Qualidade
- Checks automáticos (dw.dq_checks)
- Políticas de tolerância

5) Análises prontas
- KPIs diários
- Ticket médio por tipo
- Saldo médio
- Cohort por data de abertura

6) Reproducibilidade
- Script de geração fake
- Parâmetros de seed
- Exports CSV

7) Roadmap
- Incremental load por watermark (já aplicado)
- Particionamento por mês (já aplicado)
- CDC via WAL (já documentado)
- Observabilidade com SLIs/SLOs
