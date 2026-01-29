# Pipeline

Resumo
- Fonte: ledger_db (core bancario)
- Destino: warehouse_db (schema dw)
- Orquestracao: Airflow (DAG ledger_etl)
- Modelagem: dbt

Passos
1) create_schema
   - habilita dblink
   - cria schema dw
2) create_tables
   - cria tabelas dw.* e dq_checks
   - cria tabelas particionadas dw.transactions_p e dw.postings_p
   - cria dw.cdc_events para eventos CDC
3) load_users
4) load_accounts
5) load_transactions
6) load_postings
7) load_kyc
8) data_quality
   - postings_balance (sum(postings.amount) = 0)
   - orphan_postings (postings sem transaction)
   - accounts_without_users (accounts sem users)
   - postings_vs_balance (saldo vs soma postings)
   - transactions_without_postings (transacao sem posting)

Incremental (futuro)
- migrar para cargas incrementais por timestamp
- usar watermarks por transaction.timestamp

Observabilidade
- Airflow DAG status
- dw.dq_checks para auditoria
