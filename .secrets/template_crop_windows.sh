#!/bin/bash

# To set env. variable you need an administrator Command prompt
setx PYTHONPATH ""

setx FLASK_APP "crop_app.py"

# Azure resources
setx CROP_SUBSCRIPTION_ID "<<<replaceme>>" # Azure subscription ID

setx CROP_RG_NAME "<<<replaceme>>" # Azure resource group name

setx CROP_STORAGE_ACCOUNT CROP_RG_NAME"storage" # Azure storage account name

setx CROP_SQL_SERVER CROP_RG_NAME"sqlserver" # Azure PostgreSQL server name
setx CROP_SQL_HOST CROP_SQL_SERVER".postgres.database.azure.com" # Azure PostgreSQL host address
setx CROP_SQL_USERNAME "<<<replaceme>>" # Azure PostgreSQL admin username
setx CROP_SQL_USER CROP_SQL_USERNAME"@"CROP_SQL_SERVER
setx CROP_SQL_PASS "<<<replaceme>>" # Azure PostgreSQL admin password
setx CROP_SQL_DBNAME "<<<replaceme>>" # Azure PostgreSQL DB name
setx CROP_SQL_PORT "<<<replaceme>>" # port number to connect to the Azure PostgreSQL DB
setx CROP_SQL_WHITEIPS "<<<replaceme>>" # list of ips to be whitelisted for connecting to the Azure PostgreSQL DB

setx CROP_SQL_READER_USER  "<<<replaceme>>" # Azure PostgreSQL Read-only user name
setx CROP_SQL_READER_PASS  "<<<replaceme>>" # Azure PostgreSQL Read-only user password

# Stark
setx CROP_STARK_USERNAME "<<<replaceme>>"
setx CROP_STARK_PASS "<<<replaceme>>"

# Docker
setx CROP_DOCKER_USER "<<<replaceme>>"
setx CROP_DOCKER_PASS "<<<replaceme>>"

# 30MHz
setx CROP_30MHZ_ORGANIZATION "<<<replaceme>>"
setx CROP_30MHZ_APIKEY "<<<replaceme>>"