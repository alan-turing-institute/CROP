#!/bin/bash

source ./secrets/azure.sh 
python3 upload_sensor_data.py --source $1 --target $2
