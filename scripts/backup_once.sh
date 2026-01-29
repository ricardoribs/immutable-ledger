#!/bin/sh
set -e

TS=$(date +"%Y%m%d%H%M%S")
FILE="/backups/ledger_${TS}.sql.gz"

PGHOST=${PGHOST:-ledger_db}
PGUSER=${PGUSER:-postgres}
PGPASSWORD=${PGPASSWORD:-postgres}
PGDATABASE=${PGDATABASE:-ledger_core}

mkdir -p /backups
PGPASSWORD="$PGPASSWORD" pg_dump -h "$PGHOST" -U "$PGUSER" "$PGDATABASE" | gzip > "$FILE"

aws --endpoint-url "$S3_ENDPOINT" s3 cp "$FILE" "s3://$S3_BUCKET/$(basename "$FILE")"

if [ -n "$S3_ENDPOINT_DR" ] && [ -n "$S3_BUCKET_DR" ]; then
  aws --endpoint-url "$S3_ENDPOINT_DR" s3 cp "$FILE" "s3://$S3_BUCKET_DR/$(basename "$FILE")"
fi

# Retencao 30 dias
for obj in $(aws --endpoint-url "$S3_ENDPOINT" s3 ls "s3://$S3_BUCKET/" | awk '{print $4}'); do
  ts=$(echo "$obj" | sed -E 's/ledger_([0-9]{14})\.sql\.gz/\\1/')
  if [ -n "$ts" ]; then
    cutoff=$(date -d "30 days ago" +"%Y%m%d%H%M%S")
    if [ "$ts" -lt "$cutoff" ]; then
      aws --endpoint-url "$S3_ENDPOINT" s3 rm "s3://$S3_BUCKET/$obj"
    fi
  fi
done
