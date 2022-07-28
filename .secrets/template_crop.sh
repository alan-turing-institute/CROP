#!/bin/bash

export PYTHONPATH=`pwd`"/..:${PYTHONPATH}"

# Azure resources
export CROP_SUBSCRIPTION_ID="<<<replaceme>>" # Azure subscription ID

export CROP_RG_NAME="<<<replaceme>>" # Azure resource group name

export CROP_STORAGE_ACCOUNT=$CROP_RG_NAME"storage" # Azure storage account name

export CROP_SQL_SERVER=$CROP_RG_NAME"sqlserver" # Azure PostgreSQL server name
export CROP_SQL_HOST=$CROP_SQL_SERVER".postgres.database.azure.com" # Azure PostgreSQL host address
export CROP_SQL_USERNAME="<<<replaceme>>" # Azure PostgreSQL admin username
export CROP_SQL_USER=$CROP_SQL_USERNAME"@"$CROP_SQL_SERVER
export CROP_SQL_PASS="<<<replaceme>>" # Azure PostgreSQL admin password
export CROP_SQL_DBNAME="<<<replaceme>>" # Azure PostgreSQL DB name
export CROP_SQL_PORT="<<<replaceme>>" # port number to connect to the Azure PostgreSQL DB
export CROP_SQL_WHITEIPS="<<<replaceme>>" # list of ips to be whitelisted for connecting to the Azure PostgreSQL DB

export CROP_SQL_READER_USER="<<<replaceme>>" # Azure PostgreSQL Read-only user name
export CROP_SQL_READER_PASS="<<<replaceme>>" # Azure PostgreSQL Read-only user password

# Stark
export CROP_STARK_USERNAME="<<<replaceme>>"
export CROP_STARK_PASS="<<<replaceme>>"

# Docker
export CROP_DOCKER_USER="<<<replaceme>>"
export CROP_DOCKER_PASS="<<<replaceme>>"

# OpenWeatherData API
export CROP_OPENWEATHERMAP_APIKEY="<<replaceme>>"

# HYPER.AG
export CROP_HYPER_APIKEY="<<replaceme>>"

# GrowApp database (also need IP whitelisting)
export GROWAPP_IP="<<replaceme>>"
export GROWAPP_DATABASE="<<replaceme>>"
export GROWAPP_SCHEMA="<<replaceme>>"
export GROWAPP_USERNAME="<<replaceme>>"
export GROWAPP_PASS="<<replaceme>>"
