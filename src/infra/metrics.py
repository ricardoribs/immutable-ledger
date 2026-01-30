from prometheus_client import Histogram, Counter, Gauge


REQUEST_LATENCY = Histogram(
    "app_request_latency_seconds",
    "Request latency by endpoint",
    ["path", "method", "status"],
)

ERRORS = Counter(
    "app_errors_total",
    "Total errors by endpoint",
    ["path", "method", "status"],
)

FRAUD_DETECTED = Counter(
    "fraud_detected_total",
    "Fraud detections",
    ["action"],
)

TOTAL_BALANCE = Gauge(
    "accounts_total_balance",
    "Total balance across all accounts",
)

TRANSACTION_COUNT = Counter(
    "transactions_total",
    "Total transactions by type",
    ["operation_type"],
)

LEDGER_INTEGRITY_OK = Gauge(
    "ledger_integrity_ok",
    "Ledger integrity status (1=ok, 0=fail)",
)

LEDGER_INTEGRITY_LAST_RUN = Gauge(
    "ledger_integrity_last_run_timestamp",
    "Ledger integrity last check timestamp (epoch seconds)",
)

LEDGER_INTEGRITY_FAILURES = Counter(
    "ledger_integrity_failures_total",
    "Ledger integrity failures total",
)
