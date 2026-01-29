select
  id,
  user_id,
  account_number,
  balance,
  blocked_balance,
  overdraft_limit,
  account_type,
  status,
  created_at
from {{ source('dw', 'accounts') }}
