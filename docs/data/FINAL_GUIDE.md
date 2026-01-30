# LuisBank Data Engineering - Guia Completo

Este guia descreve a entrega final da camada de engenharia de dados do LuisBank: geração de carteira fake, ETL, modelagem dbt, snapshots, CDC, EDA e dashboards.

---

## 1) Gerar carteira fake

Comando:
```
python scripts/generate_fake_wallet.py --users 500 --days 180 --max-daily-txs 4 --export-dir analytics/exports --seed 42
```

Saídas geradas:
- analytics/exports/users.csv
- analytics/exports/accounts.csv
- analytics/exports/transactions.csv
- analytics/exports/postings.csv

---

## 2) Rodar o ETL (Airflow)

DAG: ledger_etl

O que faz:
- cria schema dw
- cria tabelas particionadas (dw.transactions_p, dw.postings_p)
- cria dw.etl_state (watermark)
- carga incremental de transactions/postings/kyc
- upsert de users/accounts
- data quality checks em dw.dq_checks

Como rodar:
- suba o Airflow no docker-compose
- abra a UI do Airflow e execute o DAG ledger_etl

---

## 3) Rodar dbt (modelagem)

Comando:
```
docker compose run --rm dbt
```

Modelos:
- staging: stg_users, stg_accounts, stg_transactions, stg_postings, stg_kyc_profiles
- marts: dim_customer, dim_account, fact_transactions, fact_postings, fact_daily_kpis
- segmentação: customer_segments

---

## 4) Rodar snapshots (dbt)

Comando:
```
docker compose run --rm dbt dbt snapshot
```

Snapshot:
- dw.account_balance_snapshot

---

## 5) CDC via WAL (opcional)

Sem aplicar no DW:
```
python scripts/cdc_wal_consumer.py
```

Aplicando eventos no DW:
```
CDC_APPLY=true CDC_WAREHOUSE_DSN="host=warehouse_db dbname=warehouse user=postgres password=postgres" CDC_OUTPUT_PLUGIN=wal2json python scripts/cdc_wal_consumer.py
```

Eventos gravados em:
- dw.cdc_events

---

## 6) EDA

Notebook:
- analytics/notebooks/eda.ipynb

---

## 7) Dashboard (Metabase)

Arquivo JSON:
- docs/data/metabase_dashboard.json

Importar:
```
METABASE_URL=http://localhost:3001 METABASE_USER=admin METABASE_PASSWORD=admin METABASE_DB=warehouse python scripts/metabase_import.py
```

---

## 8) Consultas prontas

Arquivo:
- docs/data/EXAMPLES.sql

---

## 9) Documentação para GitHub

Arquivos:
- docs/data/README.md
- docs/data/PIPELINE.md
- docs/data/DATA_DICTIONARY.md
- docs/data/EXAMPLES.sql
- docs/data/DASHBOARDS.md
- docs/data/CDC.md
- docs/data/GITHUB.md

---

## Checklist de entrega

- [x] Geração de dados fake
- [x] ETL incremental com watermark
- [x] DW particionado
- [x] dbt staging + marts
- [x] dbt snapshots
- [x] CDC via WAL
- [x] EDA notebook
- [x] Dashboard Metabase
- [x] Documentação completa
