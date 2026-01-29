# LuisBank Data Engineering

Objetivo
- Gerar uma carteira fake de clientes e transacoes
- Extrair dados do core bancario para o warehouse
- Modelar dados com dbt (staging + marts)
- Documentar KPI, qualidade e segmentacao

Fluxo
1) Geracao de dados fake (scripts/generate_fake_wallet.py)
2) ETL diario via Airflow (analytics/airflow/dags/etl_ledger.py)
3) Modelagem dbt (analytics/dbt/models)
4) Consultas e dashboards (Metabase/Grafana)
5) EDA com notebook (analytics/notebooks/eda.ipynb)
6) Snapshots (dbt snapshots)
7) CDC (docs/data/CDC.md)

Gerar carteira fake
- Exemplo:
  python scripts/generate_fake_wallet.py --users 500 --days 180 --max-daily-txs 4 --export-dir analytics/exports --seed 42

Rodar ETL (Airflow)
- DAG: ledger_etl
- Carrega dados do core (ledger_db) para o warehouse (warehouse_db)
- Cria tabelas em schema dw
- Incremental: transacoes/postings/kyc por watermark (dw.etl_state)
- Particionamento real por mes (dw.transactions_p, dw.postings_p)

Rodar dbt
- Exemplo (container dbt do docker-compose):
  docker compose run --rm dbt

Snapshots
- Exemplo:
  docker compose run --rm dbt dbt snapshot

CDC
- Exemplo:
  python scripts/cdc_wal_consumer.py
- Para gravar no DW:
  CDC_APPLY=true CDC_WAREHOUSE_DSN="host=warehouse_db dbname=warehouse user=postgres password=postgres"
- Para aplicar eventos com wal2json:
  CDC_OUTPUT_PLUGIN=wal2json

Outputs esperados
- Tabelas DW: dw.users, dw.accounts, dw.transactions_p, dw.postings_p, dw.kyc_profiles, dw.cdc_events
- Dimensoes: dim_customer, dim_account
- Fatos: fact_transactions, fact_postings, fact_daily_kpis
- Segmentos: customer_segments
- Snapshots: dw.account_balance_snapshot

Qualidade de dados
- dw.dq_checks armazena resultados de checks basicos
- Verificar postings_balance, orphan_postings, accounts_without_users

Dashboards
- docs/data/DASHBOARDS.md
- docs/data/metabase_dashboard.json
- scripts/metabase_import.py
