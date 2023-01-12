#!/bin/bash

export LC_ALL=C.UTF-8
export LANG=C.UTF-8

export FLASK_APP=crop_app.py
export FLASK_ENV=development

export PYTHONPATH=`pwd`"/..:${PYTHONPATH}"

if test -f "../.secrets/crop.sh"; then
    source ../.secrets/crop.sh
fi


npm install

# start nginx HTTP server / reverse proxy
nginx
# start gunicorn WSGI server
gunicorn --limit-request-line 0 'crop_app:app'
