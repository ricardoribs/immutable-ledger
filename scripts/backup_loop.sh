#!/bin/sh
set -e

while true; do
  /scripts/backup_once.sh
  sleep 3600
done
