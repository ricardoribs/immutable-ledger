select
  account_id,
  count(*) as total_tx,
  sum(amount) as total_amount
from {{ ref('fact_transactions') }}
group by account_id
