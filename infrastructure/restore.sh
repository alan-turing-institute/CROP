#!/bin/bash
# A script for restoring a dump of the CROP database. Only restores data,
# assumes the schema is already in place. The restoration is done
# table-by-table in an order that satisfies foreign key constraints.
# Arguments, in order:
#   postgres server host
#   port
#   dbname
#   username
#   password
#   filename for the database dump to restore
#
# See also dump.sh.
host=$1
port=$2
dbname=$3
username=$4
password=$5
filename=$6
tables_in_order=(User crop_types locations model sensor_types warning_types weather_forecast sensors batches model_scenario sensor_upload_log advanticsys_data aegis_irrigation_data aranet_airvelocity_data aranet_co2_data aranet_trh_data batch_events iweather model_measure sensor_location tinytag_data utc_energy_data warnings model_run harvests model_product model_value)

for table in ${tables_in_order[*]}
do
    echo Restoring table $table
    PGPASSWORD=$password pg_restore --host=$host --port=$port --dbname=$dbname --username=$username --no-password --single-transaction --section=data -t $table $filename
    success=$?
    if [ $success != 0 ]; then
        echo Failed to restore $table
    else
        echo Restored $table
    fi
    id_seq=${table}_id_seq
    echo Resetting the id sequence for $table
    reset_cmd="SELECT SETVAL('\"${table}_id_seq\"', (SELECT MAX(\"id\") FROM \"${table}\"));"
    psql "host=${host} port=${port} dbname=${dbname} user=${username} password=${password}" -c "$reset_cmd"
    if [ $success != 0 ]; then
        echo Failed to reset id sequence for $table
    else
        echo Reset id sequence for $table
    fi
done
exit 0
