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
