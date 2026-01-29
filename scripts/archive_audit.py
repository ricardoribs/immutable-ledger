import os
import io
import csv
from datetime import datetime, timedelta

import boto3
from sqlalchemy import select

from src.core.config import settings
from src.infra.database import SessionLocal
from src.domain.ledger.models import AuditLog


def archive_old_audit_logs():
    cutoff = datetime.utcnow() - timedelta(days=settings.AUDIT_RETENTION_DAYS)
    s3_endpoint = settings.AUDIT_ARCHIVE_S3_ENDPOINT
    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    if not s3_endpoint or not aws_access_key_id or not aws_secret_access_key:
        raise RuntimeError("AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY/AUDIT_ARCHIVE_S3_ENDPOINT nao configurados")
    s3 = boto3.client(
        "s3",
        endpoint_url=s3_endpoint,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
    )
    bucket = settings.AUDIT_ARCHIVE_S3_BUCKET
    try:
        s3.create_bucket(Bucket=bucket)
    except Exception:
        pass

    with SessionLocal() as db:
        stmt = select(AuditLog).where(AuditLog.timestamp < cutoff)
        rows = db.execute(stmt).scalars().all()
        if not rows:
            return 0

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "user_id", "action", "method", "path", "details", "ip", "user_agent", "timestamp", "prev_hash", "record_hash"])
        for r in rows:
            writer.writerow([
                r.id, r.user_id, r.action, r.method, r.path, r.details,
                r.ip_address, r.user_agent, r.timestamp.isoformat(),
                r.prev_hash, r.record_hash
            ])

        key = f"audit_archive_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.csv"
        s3.put_object(Bucket=bucket, Key=key, Body=output.getvalue().encode("utf-8"))

        for r in rows:
            db.delete(r)
        db.commit()
        return len(rows)


if __name__ == "__main__":
    archived = archive_old_audit_logs()
    print(f"Archived {archived} audit logs")
