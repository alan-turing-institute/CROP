#!/bin/bash

curl -X GET "https://api.30mhz.com/api/check/organization/$CROP_30MHZ_ORGANIZATION" \
    -H 'Content-Type: application/json' \
    -H "Authorization: $CROP_30MHZ_APIKEY"
