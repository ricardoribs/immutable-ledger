select
  t.id as transaction_id,
  t.account_id,
  a.user_id,
  a.account_type,
  t.amount,
  t.operation_type,
  t.description,
  t.timestamp,
  t.tx_date,
  t.sequence,
  t.prev_hash,
  t.record_hash
from {{ ref('stg_transactions') }} t
left join {{ ref('stg_accounts') }} a on a.id = t.account_id
