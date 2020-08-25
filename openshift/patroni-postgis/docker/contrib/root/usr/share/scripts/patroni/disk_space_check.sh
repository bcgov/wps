#!/usr/bin/env bash
set -Eeu
set -o pipefail

# Check if the available disk space on /home/postgres/pgdata has dropped
# below a critical amount ($LIMIT). If it has, it will send a notification
# on rocket chat.

if [[ -z "$AUTH_TOKEN" ]]; then
    echo "Must provide (rocket-chat) AUTH_TOKEN in environment" 1>&2
    exit 0
fi

if [[ -z "$USER_ID" ]]; then
    echo "Must provide (rocket-chat) USER_ID in environment" 1>&2
    exit 0
fi

if [[ -z "$CHANNEL" ]]; then
    echo "Must provide (rocket-chat) CHANNEL in environment" 1>&2
    exit 0
fi

if [[ -z "$LIMIT" ]]; then
    echo "Must provide LIMIT (in kilobytes) in environment" 1>&2
    exit 0
fi

send_notification() {
    local TEXT="Running low on space. $1 < $2"
    echo $TEXT
    local COMMAND="curl -v \
        -H 'X-Auth-Token: ${AUTH_TOKEN}' \
        -H 'X-User-Id: ${USER_ID}' \
        -H 'Content-Type: application/json' \
        https://chat.pathfinder.gov.bc.ca/api/v1/chat.postMessage \
        -d '{\"channel\": \"${CHANNEL}\", \"text\": \"${TEXT}\"}'"
    echo $COMMAND
    eval $COMMAND
}

FREE_SPACE=$(df /home/postgres/pgdata --output=avail | tail -n 1)
if (($FREE_SPACE < $LIMIT))
then
    send_notification $FREE_SPACE $LIMIT
    exit 1
else
    echo "$FREE_SPACE > $LIMIT : all is well"
    exit 0
fi

exit 0