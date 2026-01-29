select
  a.id as account_id,
  a.user_id,
  a.account_number,
  a.account_type,
  a.status,
  a.balance,
  a.blocked_balance,
  a.overdraft_limit,
  a.created_at,
  u.name as user_name,
  u.email as user_email
from {{ ref('stg_accounts') }} a
left join {{ ref('stg_users') }} u on u.id = a.user_id
