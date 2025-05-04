#!/bin/bash

# script used to query and monitor if / when camera streams stop

usage() { 
    echo "Monitor Event Notification:"
    echo "  -u frigate url"
    echo "  -w: Webhook URL"
    
}

URL=""
MATTERMOST_HOOK=""
while getopts ":u:w:" o; do
    case "${o}" in
        u) URL=${OPTARG};;
        w) MATTERMOST_HOOK=${OPTARG};;
        *) usage;;
    esac
done

sendMsg() {
    NAME=$1
    TEXT="Monitor: ${NAME} Connection Lost!"

    curl -i -X POST -H "Content-Type: application/json" -d '{ "text": "'"${TEXT}"'" }' ${MATTERMOST_HOOK}
}

stats=$(curl -s "${URL}/api/stats")

cameras=($(echo "$stats" | jq ".keys"))

cameras=$(echo "$stats" | jq -r ".cameras | keys[]")

for cam in $cameras; do
    fps=$(echo "$stats" | jq ".cameras.${cam}.camera_fps")
    if [ $fps == 0 ]; then
        sendMsg $cam
    fi
done
