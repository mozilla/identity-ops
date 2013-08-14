#!/bin/bash

PATH=/bin:/usr/bin:/usr/local/bin
BACKUP_DIR=/data/backups
STATE="${BACKUP_DIR}.state/.state"
KEEP_DAYS=2
progname=$(basename $0)

mkdir -p $BACKUP_DIR
mkdir -p ${BACKUP_DIR}.state
chmod 0700 $BACKUP_DIR
chmod 755 ${BACKUP_DIR}.state

if ! slave_status=$(mysql -u root -Be "show slave status \G" 2>&1); then
  echo "$progname: can't determine slave status : $slave_status" >&2
  echo "$progname: aborting backup" >&2
  echo "fail" > $STATE
  echo "couldn't fetch slave status" > ${STATE}.message
  exit 1
fi

last_error=$(echo "$slave_status" | sed -n -e "s,.*Last_Error: ,,p")

for x in IO SQL; do
  if [ "$(echo "$slave_status" | sed -n -e "s,.*Slave_${x}_Running: ,,p")" != "Yes" ]; then
    last_error="$last_error / $(echo "$slave_status" | sed -n -e "s,.*Last_${x}_Error: ,,p")"
    echo "$progname: slave $x thread is not running ($last_error)" >&2
    echo "$progname: aborting backup" >&2
    echo "fail" > $STATE
    echo "slave $x thread is not running ($last_error)" > ${STATE}.message
    exit 2
  fi
done

echo "stop slave sql_thread" | mysql -NB
trap 'echo "start slave sql_thread" | mysql -NB' EXIT

slave=$(echo "show slave status" | mysql -BE)
master_host=$(echo "$slave" | awk '$1 == "Master_Host:" {print $2;}')
master_file=$(echo "$slave" | awk '$1 == "Master_Log_File:" {print $2;}')
master_pos=$(echo "$slave" | awk '$1 == "Read_Master_Log_Pos:" {print $2;}')

date=$(date +%F-%T)
backup_file="${date}_${master_host}_${master_file}_${master_pos}.sql"

mysqldump --opt --databases --master-data=2 browserid \
| gzip -c > ${BACKUP_DIR}/${backup_file}.gz
mysql_rc=${PIPESTATUS[0]}

if [ $mysql_rc -ne 0 ]; then
  echo "$progname: mysqldump: failure, rc=$mysql_rc" >&2
  echo "fail" > $STATE
  echo "mysqldump returned non zero exit code $mysql_rc" > ${STATE}.message
  exit 2
fi

find $BACKUP_DIR -type f -name '*.sql.gz' -mtime +14 -delete

echo "success" > $STATE
> ${STATE}.message
exit 0
