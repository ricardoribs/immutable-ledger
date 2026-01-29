# CDC via WAL (replicacao logica)

Visao
- Fonte: Postgres ledger_db
- Metodo: replication slot + logical decoding
- Destino: warehouse_db ou fila (Kafka)

Script base
- scripts/cdc_wal_consumer.py

Passos (exemplo conceitual)
1) Habilitar logical replication
- wal_level = logical
- max_replication_slots >= 1
- max_wal_senders >= 1

2) Criar publication
- CREATE PUBLICATION ledger_pub FOR TABLE users, accounts, transactions, postings;

3) Criar replication slot
- SELECT pg_create_logical_replication_slot('ledger_slot', 'pgoutput');

4) Consumidor
- python scripts/cdc_wal_consumer.py
- Para gravar no DW:
  - CDC_APPLY=true
  - CDC_WAREHOUSE_DSN="host=warehouse_db dbname=warehouse user=postgres password=postgres"
  - CDC_OUTPUT_PLUGIN=wal2json (se disponivel)

Notas
- Em ambiente real: garantir retention de WAL e monitorar lag
- CDC facilita near-real-time para dashboard e antifraude
