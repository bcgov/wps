#!/bin/bash
set -Eeu
#set -o pipefail

# The script run within the parent folder
cd "$( dirname "${BASH_SOURCE[0]}" )" && cd ..

source test/_functions.sh

clean_all

./test/build.sh

./test/deploy.sh
./test/update-max-connections.sh
