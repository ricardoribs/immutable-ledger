# Deploy Strategy

- Blue-Green: use separate services and swap ingress.
- Canary: deploy `ledger-api-canary` and shift traffic gradually.
- Rollback: use `kubectl rollout undo deployment/ledger-api` in CI on failure.
- Feature flags: use `/feature-flags` API to toggle features.
- Ingress: use NGINX Ingress Controller in the cluster.
