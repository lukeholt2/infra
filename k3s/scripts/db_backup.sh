#!/bin/bash

OUTPUT=$(date +%Y_%m_%d)_${DATABASE}
WEB_HOOK=""

usage() { 
    echo "Backup K8s deployed Postgres Database:"
    echo "  -d: Name of the database to be backed up"
    echo "  -b: Path to store backups"
    echo "  -n: Deployed K8s namespace"
    echo "  -p: Pod name"
    echo "  -w: Optional Webhook URL"
}

while getopts ":d:n:p:b:" o; do
    case "${o}" in
        d) DATABASE=${OPTARG};;
        n) NAMESPACE=${OPTARG};;
        p) POD_NAME=${OPTARG};;
        b) BACKUP_PATH=${OPTARG};;
        w) WEB_HOOK=${OPTARG};;
        *) usage;;
    esac
done
shift $((OPTIND-1))

if [ ! -n "$DATABASE" ] || [ ! -n "$NAMESPACE" ] || [ ! -n "$POD_NAME" ]; then
    echo 'Missing required arguments'
    usage
    exit 1
fi

sendWebHook(){
    if [ -n "$WEB_HOOK" ]; then
	curl -s -i -X POST -H 'Content-Type: application/json' -d '{"text": "'"${DATABASE}"' backup failed!. "}' "${WEB_HOOK}"
    fi
}

### Prune backups

BACKUP_DATA=$(ls "$BACKUP_PATH" | grep -P "($(date +%Y_%m_%d --date="30 days ago")).*${DATABASE}")

cd ${BACKUP_PATH}

if [ ! -z ${BACKUP_DATA} ]; then
    echo "Pruning stale backup data...${BACKUP_DATA}"
    rm ${BACKUP_DATA}
fi

DB_POD=$(kubectl -n ${NAMESPACE} get pods | grep ${POD_NAME})

kubectl -n ${NAMESPACE} exec -i ${DB_POD}  -- pg_dump -U postgres -Z 9 -F c -w ${DATABASE} > ${BACKUP_PATH}/${OUTPUT}

if [ ! -f ${BACKUP_PATH}/${OUTPUT} ] || [ $(du -h ${BACKUP_PATH}/${OUTPUT} | cut -f 1) == 0 ]; then
    sendWebHook
fi
