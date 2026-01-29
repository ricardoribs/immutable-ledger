select
  tx_date,
  count(*) as total_transactions,
  sum(amount) as total_amount,
  sum(case when operation_type = 'DEPOSIT' then amount else 0 end) as total_deposits,
  sum(case when operation_type = 'WITHDRAW' then amount else 0 end) as total_withdraws,
  sum(case when operation_type = 'TRANSFER' then amount else 0 end) as total_transfers,
  sum(case when operation_type = 'PIX' then amount else 0 end) as total_pix
from {{ ref('fact_transactions') }}
group by tx_date
order by tx_date desc
