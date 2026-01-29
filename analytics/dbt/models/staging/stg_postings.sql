select
  id,
  transaction_id,
  account_id,
  amount,
  timestamp,
  posting_date
from {{ source('dw', 'postings_p') }}
