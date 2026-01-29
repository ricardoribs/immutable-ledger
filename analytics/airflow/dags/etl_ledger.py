from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime

LEDGER_CONN = "host=ledger_db user=postgres password=postgres dbname=ledger_core"


def _dblink_select(sql: str) -> str:
    return "select * from dblink('{conn}', '{sql}') as t".format(
        conn=LEDGER_CONN,
        sql=sql.replace("'", "''"),
    )


with DAG(
    "ledger_etl",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False,
) as dag:
    create_schema = PostgresOperator(
        task_id="create_schema",
        postgres_conn_id="warehouse_db",
        sql="""
        create extension if not exists dblink;
        create schema if not exists dw;

        create table if not exists dw.etl_state (
            pipeline text,
            table_name text,
            last_run timestamp,
            primary key (pipeline, table_name)
        );
        """,
    )

    create_tables = PostgresOperator(
        task_id="create_tables",
        postgres_conn_id="warehouse_db",
        sql="""
        create table if not exists dw.users (
            id int primary key,
            name text,
            email text,
            cpf_last4 text,
            created_at timestamp,
            mfa_enabled boolean
        );

        create table if not exists dw.accounts (
            id int primary key,
            user_id int,
            account_number text,
            balance numeric(18,2),
            blocked_balance numeric(18,2),
            overdraft_limit numeric(18,2),
            account_type text,
            status text,
            created_at timestamp
        );

        create table if not exists dw.transactions_p (
            id int,
            account_id int,
            idempotency_key text,
            amount numeric(18,2),
            operation_type text,
            description text,
            timestamp timestamp,
            sequence int,
            prev_hash text,
            record_hash text,
            tx_date date,
            primary key (id, tx_date)
        ) partition by range (tx_date);

        create table if not exists dw.postings_p (
            id int,
            transaction_id int,
            account_id int,
            amount numeric(18,2),
            timestamp timestamp,
            posting_date date,
            primary key (id, posting_date)
        ) partition by range (posting_date);

        create table if not exists dw.transactions_p_default
        partition of dw.transactions_p default;

        create table if not exists dw.postings_p_default
        partition of dw.postings_p default;

        create table if not exists dw.kyc_profiles (
            id int primary key,
            user_id int,
            status text,
            risk_level text,
            created_at timestamp
        );

        create table if not exists dw.transactions_partitions (
            partition_month date primary key
        );

        create table if not exists dw.postings_partitions (
            partition_month date primary key
        );

        create table if not exists dw.dq_checks (
            run_at timestamp,
            check_name text,
            status text,
            detail text
        );

        create table if not exists dw.cdc_events (
            id bigserial primary key,
            captured_at timestamp,
            payload text
        );

        create index if not exists idx_transactions_p_account on dw.transactions_p (account_id);
        create index if not exists idx_transactions_p_date on dw.transactions_p (tx_date);
        create index if not exists idx_postings_p_account on dw.postings_p (account_id);
        create index if not exists idx_postings_p_date on dw.postings_p (posting_date);
        """,
    )

    ensure_partitions = PostgresOperator(
        task_id="ensure_partitions",
        postgres_conn_id="warehouse_db",
        sql="""
        with months as (
            select date_trunc('month', now())::date as month_start
            union all
            select (date_trunc('month', now()) - interval '1 month')::date
            union all
            select (date_trunc('month', now()) + interval '1 month')::date
        )
        insert into dw.transactions_partitions (partition_month)
        select month_start from months
        on conflict do nothing;

        insert into dw.postings_partitions (partition_month)
        select month_start from months
        on conflict do nothing;

        do $$
        declare
          m record;
          next_month date;
          tbl text;
          tbl_post text;
        begin
          for m in select partition_month from dw.transactions_partitions loop
            next_month := (m.partition_month + interval '1 month')::date;
            tbl := format('dw.transactions_p_%s', to_char(m.partition_month, 'yyyymm'));
            execute format(
              'create table if not exists %s partition of dw.transactions_p for values from (%L) to (%L)',
              tbl, m.partition_month, next_month
            );
            execute format(
              'create index if not exists %s on %s (account_id, tx_date)',
              tbl || '_acc_date_idx', tbl
            );
            execute format(
              'create index if not exists %s on %s (sequence)',
              tbl || '_seq_idx', tbl
            );
          end loop;

          for m in select partition_month from dw.postings_partitions loop
            next_month := (m.partition_month + interval '1 month')::date;
            tbl_post := format('dw.postings_p_%s', to_char(m.partition_month, 'yyyymm'));
            execute format(
              'create table if not exists %s partition of dw.postings_p for values from (%L) to (%L)',
              tbl_post, m.partition_month, next_month
            );
            execute format(
              'create index if not exists %s on %s (account_id, posting_date)',
              tbl_post || '_acc_date_idx', tbl_post
            );
            execute format(
              'create index if not exists %s on %s (transaction_id)',
              tbl_post || '_tx_idx', tbl_post
            );
          end loop;
        end $$;
        """,
    )

    load_users = PostgresOperator(
        task_id="load_users",
        postgres_conn_id="warehouse_db",
        sql=f"""
        insert into dw.users (id, name, email, cpf_last4, created_at, mfa_enabled)
        {_dblink_select("select id, name, email, cpf_last4, created_at, mfa_enabled from users")}
        as t(id int, name text, email text, cpf_last4 text, created_at timestamp, mfa_enabled boolean)
        on conflict (id) do update
        set name = excluded.name,
            email = excluded.email,
            cpf_last4 = excluded.cpf_last4,
            created_at = excluded.created_at,
            mfa_enabled = excluded.mfa_enabled;
        """,
    )

    load_accounts = PostgresOperator(
        task_id="load_accounts",
        postgres_conn_id="warehouse_db",
        sql=f"""
        insert into dw.accounts (
            id, user_id, account_number, balance, blocked_balance, overdraft_limit,
            account_type, status, created_at
        )
        {_dblink_select("select id, user_id, account_number, balance, blocked_balance, overdraft_limit, account_type, status, created_at from accounts")}
        as t(
            id int, user_id int, account_number text, balance numeric, blocked_balance numeric,
            overdraft_limit numeric, account_type text, status text, created_at timestamp
        )
        on conflict (id) do update
        set user_id = excluded.user_id,
            account_number = excluded.account_number,
            balance = excluded.balance,
            blocked_balance = excluded.blocked_balance,
            overdraft_limit = excluded.overdraft_limit,
            account_type = excluded.account_type,
            status = excluded.status,
            created_at = excluded.created_at;
        """,
    )

    load_transactions = PostgresOperator(
        task_id="load_transactions",
        postgres_conn_id="warehouse_db",
        sql=f"""
        insert into dw.transactions_p (
            id, account_id, idempotency_key, amount, operation_type, description,
            timestamp, sequence, prev_hash, record_hash, tx_date
        )
        {_dblink_select("""
            select id, account_id, idempotency_key, amount, operation_type, description,
                   timestamp, sequence, prev_hash, record_hash, cast(timestamp as date)
            from transactions
            where timestamp > coalesce(
                (select last_run from dw.etl_state where pipeline = 'ledger_etl' and table_name = 'transactions'),
                '1900-01-01'
            )
        """)}
        as t(
            id int, account_id int, idempotency_key text, amount numeric,
            operation_type text, description text, timestamp timestamp,
            sequence int, prev_hash text, record_hash text, tx_date date
        )
        on conflict do nothing;
        """,
    )

    load_postings = PostgresOperator(
        task_id="load_postings",
        postgres_conn_id="warehouse_db",
        sql=f"""
        insert into dw.postings_p (id, transaction_id, account_id, amount, timestamp, posting_date)
        {_dblink_select("""
            select id, transaction_id, account_id, amount, timestamp, cast(timestamp as date)
            from postings
            where timestamp > coalesce(
                (select last_run from dw.etl_state where pipeline = 'ledger_etl' and table_name = 'postings'),
                '1900-01-01'
            )
        """)}
        as t(id int, transaction_id int, account_id int, amount numeric, timestamp timestamp, posting_date date)
        on conflict do nothing;
        """,
    )

    load_kyc = PostgresOperator(
        task_id="load_kyc",
        postgres_conn_id="warehouse_db",
        sql=f"""
        insert into dw.kyc_profiles (id, user_id, status, risk_level, created_at)
        {_dblink_select("""
            select id, user_id, status, risk_level, created_at
            from kyc_profiles
            where created_at > coalesce(
                (select last_run from dw.etl_state where pipeline = 'ledger_etl' and table_name = 'kyc_profiles'),
                '1900-01-01'
            )
        """)}
        as t(id int, user_id int, status text, risk_level text, created_at timestamp)
        on conflict (id) do update
        set status = excluded.status,
            risk_level = excluded.risk_level,
            created_at = excluded.created_at;
        """,
    )

    update_watermarks = PostgresOperator(
        task_id="update_watermarks",
        postgres_conn_id="warehouse_db",
        sql="""
        insert into dw.etl_state (pipeline, table_name, last_run)
        values
          ('ledger_etl', 'transactions', now()),
          ('ledger_etl', 'postings', now()),
          ('ledger_etl', 'kyc_profiles', now())
        on conflict (pipeline, table_name) do update
        set last_run = excluded.last_run;
        """,
    )

    data_quality = PostgresOperator(
        task_id="data_quality",
        postgres_conn_id="warehouse_db",
        sql="""
        insert into dw.dq_checks (run_at, check_name, status, detail)
        select now(), 'postings_balance',
               case when exists (
                    select 1 from (
                        select transaction_id, sum(amount) as total
                        from dw.postings_p
                        group by transaction_id
                    ) s where abs(total) > 0.01
               ) then 'fail' else 'pass' end,
               'sum(postings.amount) should be 0 per transaction';

        insert into dw.dq_checks (run_at, check_name, status, detail)
        select now(), 'orphan_postings',
               case when exists (
                    select 1 from dw.postings_p p
                    left join dw.transactions_p t on t.id = p.transaction_id
                    where t.id is null
               ) then 'fail' else 'pass' end,
               'postings must reference transactions';

        insert into dw.dq_checks (run_at, check_name, status, detail)
        select now(), 'accounts_without_users',
               case when exists (
                    select 1 from dw.accounts a
                    left join dw.users u on u.id = a.user_id
                    where u.id is null
               ) then 'fail' else 'pass' end,
               'accounts must have users';

        insert into dw.dq_checks (run_at, check_name, status, detail)
        select now(), 'postings_vs_balance',
               case when exists (
                    select 1
                    from (
                        select a.id, a.balance, coalesce(sum(p.amount), 0) as postings_sum
                        from dw.accounts a
                        left join dw.postings_p p on p.account_id = a.id
                        group by a.id, a.balance
                    ) s
                    where abs(s.balance - s.postings_sum) > 0.01
               ) then 'warn' else 'pass' end,
               'accounts.balance should match sum(postings.amount)';

        insert into dw.dq_checks (run_at, check_name, status, detail)
        select now(), 'transactions_without_postings',
               case when exists (
                    select 1 from dw.transactions_p t
                    left join dw.postings_p p on p.transaction_id = t.id
                    where p.id is null
               ) then 'fail' else 'pass' end,
               'transactions must have postings';
        """,
    )

    create_schema >> create_tables >> ensure_partitions >> load_users >> load_accounts >> load_transactions >> load_postings >> load_kyc >> update_watermarks >> data_quality
