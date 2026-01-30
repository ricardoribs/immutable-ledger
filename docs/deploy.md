# Deploy Strategy

- Blue-Green: use separate services and swap ingress.
- Canary: deploy `ledger-api-canary` and shift traffic gradually.
- Rollback: use `kubectl rollout undo deployment/ledger-api` in CI on failure.
- Feature flags: use `/feature-flags` API to toggle features.
- Ingress: use NGINX Ingress Controller in the cluster.

## Migrações controladas (CI/CD)
- O pipeline executa `scripts/db_migrate.py` via Job Kubernetes antes do deploy.
- `SEED_DEV=false` em staging/prod para evitar dados de teste.
- Em dev local, `SEED_DEV=true` pode ser usado para criar dados de seed.
