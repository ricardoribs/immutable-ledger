{% snapshot account_balance_snapshot %}

{{
  config(
    target_schema='dw',
    unique_key='account_id',
    strategy='check',
    check_cols=['balance', 'blocked_balance', 'overdraft_limit', 'status']
  )
}}

select
  account_id,
  user_id,
  balance,
  blocked_balance,
  overdraft_limit,
  status
from {{ ref('dim_account') }}

{% endsnapshot %}
