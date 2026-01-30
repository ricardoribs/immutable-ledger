import os
import secrets
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Ele DEVE pegar do ambiente (evite credenciais fixas no repositorio)
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://user:pass@localhost:5432/ledger_core"
    )
    
    REDIS_URL = os.getenv("REDIS_URL", "redis://ledger_redis:6379/0")

    STRICT_SECURITY = os.getenv("STRICT_SECURITY", "false").lower() in {"1", "true", "yes"}

    SECRET_KEY = os.getenv("SECRET_KEY")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

    VAULT_ADDR = os.getenv("VAULT_ADDR")
    VAULT_TOKEN = os.getenv("VAULT_TOKEN")
    VAULT_KV_MOUNT = os.getenv("VAULT_KV_MOUNT", "secret")
    VAULT_ENCRYPTION_KEY_PATH = os.getenv("VAULT_ENCRYPTION_KEY_PATH", "ledger/crypto")
    VAULT_ENCRYPTION_KEY_FIELD = os.getenv("VAULT_ENCRYPTION_KEY_FIELD", "encryption_key")

    AUDIT_RETENTION_DAYS = int(os.getenv("AUDIT_RETENTION_DAYS", "2555"))  # ~7 anos
    AUDIT_ARCHIVE_S3_BUCKET = os.getenv("AUDIT_ARCHIVE_S3_BUCKET", "ledger-audit-archive")
    AUDIT_ARCHIVE_S3_ENDPOINT = os.getenv("AUDIT_ARCHIVE_S3_ENDPOINT", "http://minio:9000")

    SYSTEM_USER_EMAIL = os.getenv("SYSTEM_USER_EMAIL", "system@ledger.local")
    SYSTEM_ACCOUNT_NUMBER = os.getenv("SYSTEM_ACCOUNT_NUMBER", "0000-0")

    SAVINGS_INTEREST_MONTHLY = float(os.getenv("SAVINGS_INTEREST_MONTHLY", "0.005"))
    IOF_RATE_FIXED = float(os.getenv("IOF_RATE_FIXED", "0.0038"))
    IOF_RATE_DAILY = float(os.getenv("IOF_RATE_DAILY", "0.000082"))
    LOAN_LATE_FEE_RATE = float(os.getenv("LOAN_LATE_FEE_RATE", "0.02"))
    LOAN_LATE_INTEREST_MONTHLY = float(os.getenv("LOAN_LATE_INTEREST_MONTHLY", "0.01"))

    KYC_REQUIRED_THRESHOLD = float(os.getenv("KYC_REQUIRED_THRESHOLD", "5000.0"))
    AML_LARGE_TX_THRESHOLD = float(os.getenv("AML_LARGE_TX_THRESHOLD", "10000.0"))

    SMTP_HOST = os.getenv("SMTP_HOST", "mailhog")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
    SMS_GATEWAY_URL = os.getenv("SMS_GATEWAY_URL", "http://sms_gateway:6001/sms")
    WHATSAPP_GATEWAY_URL = os.getenv("WHATSAPP_GATEWAY_URL", "http://whatsapp_gateway:6002/whatsapp")
    PUSH_GATEWAY_URL = os.getenv("PUSH_GATEWAY_URL", "http://push_gateway:6003/push")
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "http://slack_mock:6004/slack")
    PAGERDUTY_WEBHOOK_URL = os.getenv("PAGERDUTY_WEBHOOK_URL", "http://pagerduty_mock:6005/pagerduty")
    ALERT_ROUTER_URL = os.getenv("ALERT_ROUTER_URL", "http://alert_router:5001/alert")
    LEDGER_INTEGRITY_INTERVAL_SECONDS = int(os.getenv("LEDGER_INTEGRITY_INTERVAL_SECONDS", "300"))

    _INVALID_PLACEHOLDERS = {"CHANGEME_SECRET_KEY", "CHANGEME_ENCRYPTION_KEY", "", None}

    if STRICT_SECURITY:
        if SECRET_KEY in _INVALID_PLACEHOLDERS:
            raise RuntimeError("SECRET_KEY ausente ou insegura em STRICT_SECURITY")
        if ENCRYPTION_KEY in _INVALID_PLACEHOLDERS:
            raise RuntimeError("ENCRYPTION_KEY ausente ou insegura em STRICT_SECURITY")

    if SECRET_KEY in _INVALID_PLACEHOLDERS:
        SECRET_KEY = secrets.token_urlsafe(48)
    if ENCRYPTION_KEY in _INVALID_PLACEHOLDERS:
        ENCRYPTION_KEY = secrets.token_urlsafe(48)

settings = Settings()
