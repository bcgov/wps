#!/bin/bash
# Run the code in our python project through a linter.
# NOTE: pylint will only run in an enviroment where developer dependancies have been installed.

set -euo pipefail

## Breakdown of the command:
# python : this is our python interpreter.
# -m : run a library module as a script.
# pylint : this is the linter we use (https://www.pylint.org/).
# --rcfile=.pylintrc : we specify our lint configuration explicitly. We do this for a number of reasons:
#       1. By specifying our rcfile, we know that pylint is running in the correct folder.
#       2. By specifying our rcfile, we can configure exactly how we lint.
#           - we're overriding the default pep8 max line length and allowing 110 lines.
#           - we're whitelisting pydantic to allow for analyzing C extensions on it.
python -m pylint --rcfile=.pylintrc *.py **/*.py