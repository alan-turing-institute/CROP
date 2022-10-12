#!/bin/bash

export LC_ALL=C.UTF-8
export LANG=C.UTF-8

export FLASK_APP=crop_app.py
export FLASK_ENV=development

export PYTHONPATH=`pwd`"/..:${PYTHONPATH}"

if test -f "../.secrets/crop.sh"; then
    source ../.secrets/crop.sh
fi

if [ -n "$1" ] && [ "$1" -gt "-1" ]
then
    bport=$1
else
    bport=5000
fi

npm install
flask run --host=0.0.0.0 --port $bport
