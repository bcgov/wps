#!/bin/bash
# Run the code in our python project through a linter.

set -euo pipefail

poetry run ruff .