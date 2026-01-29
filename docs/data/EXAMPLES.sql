-- KPIs diarios
select * from fact_daily_kpis order by tx_date desc;

-- Ticket medio por tipo de operacao
select
  operation_type,
  avg(amount) as avg_amount
from fact_transactions
group by operation_type;

-- Top 10 clientes por saldo
select
  user_id,
  sum(balance) as total_balance
from dim_account
group by user_id
order by total_balance desc
limit 10;

-- Atividade por cliente (90 dias)
select
  user_id,
  count(*) as tx_count_90d,
  sum(amount) as volume_90d
from fact_transactions
where tx_date >= current_date - interval '90 days'
group by user_id
order by volume_90d desc;

-- Postings que nao fecham (devem ser zero)
select transaction_id, sum(amount) as total
from fact_postings
group by transaction_id
having abs(sum(amount)) > 0.01;
