#!/bin/bash
# A script for creating a dump of the CROP data. The result can be restored
# with restore.sh.
# Arguments, in order:
#   postgres server host
#   port
#   dbname
#   username
#   password
#   filename where to write the dump
#
# See also restore.sh.
host=$1
port=$2
dbname=$3
username=$4
password=$5
filename=$6
echo Dumping to $filename
PGPASSWORD=$password pg_dump --host=$host --port=$port --dbname=$dbname --username=$username -Fc --no-password --section=data > $filename
success=$?
if [ $success != 0 ]; then
    echo Failed generate the dump $filename
else
    echo Successfully generated the dump $filename
fi
