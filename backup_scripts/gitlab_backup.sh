#!/bin/bash

BACKUP_PATH="/mnt/backups/"
DIRECTORY=$(date +%Y_%m_%d)_config
WEB_HOOK=""

usage() { 
    echo "Backup GitLab Database:"
    echo "  -b: Path to store backups"
    echo "  -w: Optional Webhook URL"
}

while getopts ":b:w:" o; do
    case "${o}" in
        b) BACKUP_PATH=${OPTARG};;
        w) WEB_HOOK=${OPTARG};;
        *) usage;;
    esac
done
shift $((OPTIND-1))

## run gitlab backup

gitlab-backup create

## backup configs

mkdir $DIRECTORY
cp /etc/gitlab/gitlab.rb ${DIRECTORY}/
cp /etc/gitlab/gitlab-secrets.json ${DIRECTORY}/
tar -cvzf ${DIRECTORY}.tar.gz ${DIRECTORY}

mv ${DIRECTORY}.tar.gz ${BACKUP_PATH}
rm -rf ${DIRECTORY}

### Prune backups

BACKUP_DATA=$(ls ${BACKUP_PATH} | grep -P "($(date +%Y_%m_%d --date="30 days ago")).*backup")
BACKUP_CONFIG=$(ls ${BACKUP_PATH} | grep -P "($(date +%Y_%m_%d --date="30 days ago"))_config")

cd ${BACKUP_PATH}

if [ ! -z ${BACKUP_DATA} ] && [ -f ${BACKUP_DATA} ]; then
    echo "Prunning old backup data..."
    rm ${BACKUP_DATA}
fi

if [ ! -z ${BACKUP_CONFIG} ] && [ -f ${BACKUP_CONFIG} ]; then
    echo "Prunning old backup config..."
    rm ${BACKUP_CONFIG}
fi

if [ $(ls ${BACKUP_PATH} | grep -P "($(date +%Y_%m_%d)).*" | wc -l) -lt 2 ] && [ -n "$WEB_HOOK" ]; then
    curl -s -i -X POST -H 'Content-Type: application/json' -d '{"text": "GitLab backup failed!. "}' "${WEB_HOOK}"
fi
