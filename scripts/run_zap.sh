#!/bin/sh
set -e

TARGET=${1:-http://localhost:8000}
docker run --rm -t owasp/zap2docker-stable zap-baseline.py -t "$TARGET"
