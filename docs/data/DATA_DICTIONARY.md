# Data Dictionary (DW)

Tabela: dw.users
- id (int)
- name (text)
- email (text)
- cpf_last4 (text)
- created_at (timestamp)
- mfa_enabled (boolean)

Tabela: dw.accounts
- id (int)
- user_id (int)
- account_number (text)
- balance (numeric)
- blocked_balance (numeric)
- overdraft_limit (numeric)
- account_type (text)
- status (text)
- created_at (timestamp)

Tabela: dw.transactions_p (partitioned)
- id (int)
- account_id (int)
- idempotency_key (text)
- amount (numeric)
- operation_type (text)
- description (text)
- timestamp (timestamp)
- sequence (int)
- prev_hash (text)
- record_hash (text)
- tx_date (date)

Tabela: dw.postings_p (partitioned)
- id (int)
- transaction_id (int)
- account_id (int)
- amount (numeric)
- timestamp (timestamp)
- posting_date (date)

Tabela: dw.kyc_profiles
- id (int)
- user_id (int)
- status (text)
- risk_level (text)
- created_at (timestamp)

Tabela: dw.dq_checks
- run_at (timestamp)
- check_name (text)
- status (text)
- detail (text)

Tabela: dw.cdc_events
- id (bigserial)
- captured_at (timestamp)
- payload (text)

Modelos dbt
- stg_users, stg_accounts, stg_transactions, stg_postings, stg_kyc_profiles
- dim_customer, dim_account
- fact_transactions, fact_postings, fact_daily_kpis
- customer_segments
