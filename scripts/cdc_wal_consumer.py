import os
import time
import json
import psycopg2
from psycopg2.extras import LogicalReplicationConnection


def ensure_publication(conn, publication: str, tables: list[str]):
    with conn.cursor() as cur:
        cur.execute("select 1 from pg_publication where pubname = %s", (publication,))
        exists = cur.fetchone()
        if not exists:
            cur.execute(
                "create publication %s for table %s" % (
                    publication,
                    ", ".join(tables),
                )
            )
            conn.commit()


def ensure_slot(conn, slot_name: str, output_plugin: str = "pgoutput"):
    with conn.cursor() as cur:
        cur.execute("select 1 from pg_replication_slots where slot_name = %s", (slot_name,))
        exists = cur.fetchone()
        if not exists:
            cur.execute("select pg_create_logical_replication_slot(%s, %s)", (slot_name, output_plugin))
            conn.commit()


def _apply_change(wh_conn, change: dict):
    table = change.get("table")
    columns = change.get("columnnames", [])
    values = change.get("columnvalues", [])
    if not table or not columns:
        return
    row = dict(zip(columns, values))

    if table == "users":
        sql = """
            insert into dw.users (id, name, email, cpf_last4, created_at, mfa_enabled)
            values (%s, %s, %s, %s, %s, %s)
            on conflict (id) do update
            set name = excluded.name,
                email = excluded.email,
                cpf_last4 = excluded.cpf_last4,
                created_at = excluded.created_at,
                mfa_enabled = excluded.mfa_enabled
        """
        params = (
            row.get("id"),
            row.get("name"),
            row.get("email"),
            row.get("cpf_last4"),
            row.get("created_at"),
            row.get("mfa_enabled"),
        )
    elif table == "accounts":
        sql = """
            insert into dw.accounts (
                id, user_id, account_number, balance, blocked_balance,
                overdraft_limit, account_type, status, created_at
            )
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            on conflict (id) do update
            set user_id = excluded.user_id,
                account_number = excluded.account_number,
                balance = excluded.balance,
                blocked_balance = excluded.blocked_balance,
                overdraft_limit = excluded.overdraft_limit,
                account_type = excluded.account_type,
                status = excluded.status,
                created_at = excluded.created_at
        """
        params = (
            row.get("id"),
            row.get("user_id"),
            row.get("account_number"),
            row.get("balance"),
            row.get("blocked_balance"),
            row.get("overdraft_limit"),
            row.get("account_type"),
            row.get("status"),
            row.get("created_at"),
        )
    elif table == "transactions":
        tx_date = None
        if row.get("timestamp"):
            tx_date = str(row.get("timestamp"))[:10]
        sql = """
            insert into dw.transactions_p (
                id, account_id, idempotency_key, amount, operation_type,
                description, timestamp, sequence, prev_hash, record_hash, tx_date
            )
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            on conflict do nothing
        """
        params = (
            row.get("id"),
            row.get("account_id"),
            row.get("idempotency_key"),
            row.get("amount"),
            row.get("operation_type"),
            row.get("description"),
            row.get("timestamp"),
            row.get("sequence"),
            row.get("prev_hash"),
            row.get("record_hash"),
            tx_date,
        )
    elif table == "postings":
        posting_date = None
        if row.get("timestamp"):
            posting_date = str(row.get("timestamp"))[:10]
        sql = """
            insert into dw.postings_p (
                id, transaction_id, account_id, amount, timestamp, posting_date
            )
            values (%s, %s, %s, %s, %s, %s)
            on conflict do nothing
        """
        params = (
            row.get("id"),
            row.get("transaction_id"),
            row.get("account_id"),
            row.get("amount"),
            row.get("timestamp"),
            posting_date,
        )
    else:
        return

    with wh_conn.cursor() as wh_cur:
        wh_cur.execute(sql, params)


def consume_changes(replication_dsn: str, slot_name: str, publication: str, apply: bool, warehouse_dsn: str | None):
    repl_conn = psycopg2.connect(replication_dsn, connection_factory=LogicalReplicationConnection)
    cur = repl_conn.cursor()
    wh_conn = None
    if apply and warehouse_dsn:
        wh_conn = psycopg2.connect(warehouse_dsn)

    def on_message(msg):
        print("CDC:", msg.payload)
        if wh_conn:
            with wh_conn.cursor() as wh_cur:
                wh_cur.execute(
                    "insert into dw.cdc_events (captured_at, payload) values (now(), %s)",
                    (msg.payload,),
                )
            try:
                data = json.loads(msg.payload)
                for change in data.get("change", []):
                    _apply_change(wh_conn, change)
            except Exception:
                pass
            wh_conn.commit()
        msg.cursor.send_feedback(flush_lsn=msg.data_start)

    cur.start_replication(
        slot_name=slot_name,
        options={"proto_version": "1", "publication_names": publication},
        decode=True,
    )

    try:
        cur.consume_stream(on_message)
    except KeyboardInterrupt:
        print("CDC finalizado")
    finally:
        cur.close()
        repl_conn.close()
        if wh_conn:
            wh_conn.close()


if __name__ == "__main__":
    host = os.getenv("CDC_HOST", "ledger_db")
    dbname = os.getenv("CDC_DB", "ledger_core")
    user = os.getenv("CDC_USER", "postgres")
    password = os.getenv("CDC_PASSWORD")
    publication = os.getenv("CDC_PUBLICATION", "ledger_pub")
    slot_name = os.getenv("CDC_SLOT", "ledger_slot")
    apply = os.getenv("CDC_APPLY", "false").lower() == "true"
    warehouse_dsn = os.getenv("CDC_WAREHOUSE_DSN")
    output_plugin = os.getenv("CDC_OUTPUT_PLUGIN", "pgoutput")

    if not password:
        raise RuntimeError("CDC_PASSWORD nao configurado")
    if not warehouse_dsn:
        raise RuntimeError("CDC_WAREHOUSE_DSN nao configurado")
    dsn = f"host={host} dbname={dbname} user={user} password={password}"
    conn = psycopg2.connect(dsn)

    ensure_publication(conn, publication, [
        "users",
        "accounts",
        "transactions",
        "postings",
    ])
    ensure_slot(conn, slot_name, output_plugin=output_plugin)
    conn.close()

    replication_dsn = dsn + " replication=database"
    time.sleep(2)
    consume_changes(replication_dsn, slot_name, publication, apply, warehouse_dsn if apply else None)
