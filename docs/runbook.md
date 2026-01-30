# Disaster Recovery Runbook

## Objectives
- RPO < 1 hour
- RTO < 4 hours
- Streaming replica: use `ledger_db_replica` for dev DR simulation.
- Second region simulation: `ledger_db_region2` and `minio_dr`.

## Backup
- Automated daily backup to MinIO (S3-compatible).
- Retention: 30 days (bucket lifecycle to be configured in MinIO/production S3).

## Restore (Test)
1. Run `scripts/restore_test.sh` inside the backup container.
2. Validate API health and key ledger queries.

## Failover (Dev)
1. Start a fresh Postgres container.
2. Restore latest backup.
3. Repoint `DATABASE_URL` and restart API and workers.

## Alertas críticos
- **Integridade do ledger:** `LedgerIntegrityFailed` ou `LedgerIntegrityStale`.
- **Redis fora:** `RedisDown` (rate limit deve falhar fechado em produção).
- **Banco fora:** `DatabaseDown`.
