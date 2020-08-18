#!/bin/bash
# Run the unit tests for our python project.

set -euo pipefail

## Breakdown of the test command:
# - python : this is the python interpreter.
# - m : run library module as a script.
# - unittest : the module we use to run unit tests.

# NOTE: the unittest require the ORIGINS environment variable to be set!
python -m unittest