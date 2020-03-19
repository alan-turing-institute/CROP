#!/bin/bash

export FLASK_APP=crop_app.py
source ../.secrets/crop.sh

flask run --host=0.0.0.0
