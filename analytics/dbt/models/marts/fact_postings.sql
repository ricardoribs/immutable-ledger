select
  p.id as posting_id,
  p.transaction_id,
  p.account_id,
  a.user_id,
  p.amount,
  p.timestamp,
  p.posting_date
from {{ ref('stg_postings') }} p
left join {{ ref('stg_accounts') }} a on a.id = p.account_id
