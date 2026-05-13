#!/usr/bin/env bash
set -euo pipefail
for i in $(seq 2 21); do
  sudo ifconfig lo0 alias 127.0.0.$i 2>/dev/null || echo "127.0.0.$i may already exist" >&2
done
echo "Added IP aliases 127.0.0.2-127.0.0.21 on lo0"
echo "Note: --local-ips is Linux-only in k6. On macOS, X-Forwarded-For header is used for Kong IP simulation."
