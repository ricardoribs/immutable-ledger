# Trade-offs Arquiteturais

## Ledger append-only vs event sourcing
- **Escolha atual:** ledger append-only com transações + postings e encadeamento por hash.
- **Ganhos:** leitura simples, auditoria direta, menor complexidade operacional.
- **Custos:** menos flexibilidade para reprocessar estados, menor capacidade de replay completo.
- **Mitigação:** verificação periódica de integridade e reconciliação automática.

## Consistência forte vs eventual
- **Escolha atual:** consistência forte nas operações críticas (saldo/transferências).
- **Ganhos:** evita double-spend e inconsistências contábeis.
- **Custos:** menor throughput em picos e maior latência em regiões remotas.
- **Mitigação:** cache de leitura com TTL curto e limites operacionais.

## Cache de saldo vs cálculo integral
- **Escolha atual:** saldo por soma de postings com cache de leitura.
- **Ganhos:** performance para endpoints de saldo/extrato.
- **Custos:** risco de cache stale por curto período.
- **Mitigação:** invalidação de cache após commit e TTL baixo.

## Idempotência via Redis
- **Escolha atual:** idempotência baseada em Redis + chave por conta.
- **Ganhos:** evita duplicação em retry e integra com rate limit.
- **Custos:** dependência do cache para deduplicação rápida.
- **Mitigação:** fallback por busca no banco em caso de hit e controle de janela.
