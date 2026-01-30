# LuisBank Data Engineering

Objetivo
- Gerar uma carteira fake de clientes e transações
- Extrair dados do core bancário para o warehouse
- Modelar dados com dbt (staging + marts)
- Documentar KPI, qualidade e segmentação

Fluxo
1) Geração de dados fake (scripts/generate_fake_wallet.py)
2) ETL diário via Airflow (analytics/airflow/dags/etl_ledger.py)
3) Modelagem dbt (analytics/dbt/models)
4) Consultas e dashboards (Metabase/Grafana)
5) EDA com notebook (analytics/notebooks/eda.ipynb)

Gerar carteira fake
- Exemplo:
  python scripts/generate_fake_wallet.py --users 500 --days 180 --max-daily-txs 4 --export-dir analytics/exports --seed 42

Rodar ETL (Airflow)
- DAG: ledger_etl
- Carrega dados do core (ledger_db) para o warehouse (warehouse_db)
- Cria tabelas em schema dw

Rodar dbt
- Exemplo (container dbt do docker-compose):
  docker compose run --rm dbt

Outputs esperados
- Tabelas DW: dw.users, dw.accounts, dw.transactions, dw.postings, dw.kyc_profiles
- Dimensões: dim_customer, dim_account
- Fatos: fact_transactions, fact_postings, fact_daily_kpis
- Segmentos: customer_segments

Qualidade de dados
- dw.dq_checks armazena resultados de checks básicos
- Verificar postings_balance, orphan_postings, accounts_without_users
