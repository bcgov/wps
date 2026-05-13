#!/usr/bin/env bash
set -euo pipefail
for i in $(seq 2 21); do
  sudo ifconfig lo0 -alias 127.0.0.$i 2>/dev/null || echo "127.0.0.$i not found, skipping" >&2
done
echo "Removed IP aliases 127.0.0.2-127.0.0.21 from lo0"
