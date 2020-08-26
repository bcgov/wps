#!/usr/bin/env bash
set -Eeu
set -o pipefail

# Check if the available disk space on /home/postgres/pgdata has dropped
# below a critical amount ($DISK_SPACE_WARNING_LIMIT). If it has, it will send a notification
# on rocket chat.

if [[ -z "$ROCKET_AUTH_TOKEN" ]]; then
    echo "Must provide (rocket-chat) ROCKET_AUTH_TOKEN in environment" 1>&2
    exit 0
fi

if [[ -z "$ROCKET_USER_ID" ]]; then
    echo "Must provide (rocket-chat) ROCKET_USER_ID in environment" 1>&2
    exit 0
fi

if [[ -z "$ROCKET_CHANNEL" ]]; then
    echo "Must provide (rocket-chat) ROCKET_CHANNEL in environment" 1>&2
    exit 0
fi

if [[ -z "$DISK_SPACE_WARNING_LIMIT" ]]; then
    echo "Must provide DISK_SPACE_WARNING_LIMIT (in kilobytes) in environment" 1>&2
    exit 0
fi

send_notification() {
    local TEXT="$(hostname) is running low on space: $1 < $2"
    echo $TEXT
    local COMMAND="curl -v \
        -H 'X-Auth-Token: ${ROCKET_AUTH_TOKEN}' \
        -H 'X-User-Id: ${ROCKET_USER_ID}' \
        -H 'Content-Type: application/json' \
        https://chat.pathfinder.gov.bc.ca/api/v1/chat.postMessage \
        -d '{\"channel\": \"${ROCKET_CHANNEL}\", \"text\": \"${TEXT}\"}'"
    echo $COMMAND
    eval $COMMAND
}

DRIVE=${DRIVE:-/home/postgres/pgdata}
FREE_SPACE=$(df $DRIVE --output=avail | tail -n 1)
if (($FREE_SPACE < $DISK_SPACE_WARNING_LIMIT))
then
    send_notification $FREE_SPACE $DISK_SPACE_WARNING_LIMIT
    exit 1
else
    echo "$(hostname): $FREE_SPACE > $DISK_SPACE_WARNING_LIMIT : all is well"
    exit 0
fi

exit 0