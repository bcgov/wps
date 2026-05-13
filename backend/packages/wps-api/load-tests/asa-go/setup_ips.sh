#!/usr/bin/env bash
set -euo pipefail
for i in $(seq 2 21); do
  sudo ip addr add 127.0.0.$i/8 dev lo 2>/dev/null || echo "127.0.0.$i already exists, skipping" >&2  # /8 matches loopback network prefix
done
echo "Added IP aliases 127.0.0.2-127.0.0.21 on lo"
