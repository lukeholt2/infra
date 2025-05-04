#!/bin/bash

OUTPUT=$(date +%Y_%m_%d)_${DATABASE}

usage() { 
    echo "Backup Postgres Database:"
    echo "  -d: Name of the database to be backed up"
    echo "  -b: Path to store backups"
    echo "  -w: Optional Webhook URL"
}

while getopts ":d:b:" o; do
    case "${o}" in
        d) DATABASE=${OPTARG};;
        b) BACKUP_PATH=${OPTARG};;
        w) WEB_HOOK=${OPTARG};;
        *) usage;;
    esac
done
shift $((OPTIND-1))

### Prune backups

BACKUP_DATA=$(ls "$BACKUP_PATH" | grep -P "($(date +%Y_%m_%d --date="30 days ago")).*${DATABASE}")

cd ${BACKUP_PATH}

if [ ! -z ${BACKUP_DATA} ]; then
    echo "Prunning stale backup data...${BACKUP_DATA}"
    rm ${BACKUP_DATA}
fi

pg_dump -U postgres -Z 9 -F c -w ${DATABASE} > ${BACKUP_PATH}/${OUTPUT}

if [ ! -f ${BACKUP_PATH}/${OUTPUT} ] && [ -n "$WEB_HOOK" ]; then
    curl -s -i -X POST -H 'Content-Type: application/json' -d '{"text": "'"${DATABASE}"' backup failed!. "}' "${WEB_HOOK}"
fi
