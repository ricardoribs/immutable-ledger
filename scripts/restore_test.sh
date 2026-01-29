#!/bin/sh
set -e

LATEST=$(aws --endpoint-url "$S3_ENDPOINT" s3 ls "s3://$S3_BUCKET/" | tail -n 1 | awk '{print $4}')
if [ -z "$LATEST" ]; then
  echo "No backups found"
  exit 1
fi

aws --endpoint-url "$S3_ENDPOINT" s3 cp "s3://$S3_BUCKET/$LATEST" /tmp/restore.sql.gz
gunzip -c /tmp/restore.sql.gz | PGPASSWORD="$PGPASSWORD" psql -h "$PGHOST" -U "$PGUSER" "$PGDATABASE" >/dev/null
echo "Restore test completed"
