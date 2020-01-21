#!/bin/bash

source azure_auth.sh 
python3 upload_sensor_data.py --source $1 --target $2
