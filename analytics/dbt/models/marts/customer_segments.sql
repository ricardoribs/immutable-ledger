with recent as (
  select
    user_id,
    count(*) as tx_count_90d,
    sum(amount) as volume_90d
  from {{ ref('fact_transactions') }}
  where tx_date >= current_date - interval '90 days'
  group by user_id
),
current_balance as (
  select user_id, sum(balance) as total_balance
  from {{ ref('dim_account') }}
  group by user_id
)
select
  c.user_id,
  c.name,
  coalesce(r.tx_count_90d, 0) as tx_count_90d,
  coalesce(r.volume_90d, 0) as volume_90d,
  coalesce(b.total_balance, 0) as total_balance,
  case
    when coalesce(b.total_balance, 0) >= 10000 and coalesce(r.tx_count_90d, 0) >= 20 then 'high_value'
    when coalesce(r.tx_count_90d, 0) >= 10 then 'active'
    when coalesce(r.tx_count_90d, 0) >= 1 then 'occasional'
    else 'inactive'
  end as segment
from {{ ref('dim_customer') }} c
left join recent r on r.user_id = c.user_id
left join current_balance b on b.user_id = c.user_id
