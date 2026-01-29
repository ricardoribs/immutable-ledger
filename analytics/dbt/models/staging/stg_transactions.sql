select
  id,
  account_id,
  idempotency_key,
  amount,
  operation_type,
  description,
  timestamp,
  sequence,
  prev_hash,
  record_hash,
  tx_date
from {{ source('dw', 'transactions_p') }}
