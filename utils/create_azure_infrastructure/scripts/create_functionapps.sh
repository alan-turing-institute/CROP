#!/bin/bash

###################################################################################
# Creates Function App(s)
#
#
# Prerequisites
# =============
# Azure CLI (install via homebrew):
#     brew update && brew install azure-cli
#     az login
#     az account set --subscription <subscriptionID>
# Azure Functions Core Tools - (install via homebrew):
#    brew tap azure/functions
#    brew install azure-functions-core-tools@4
###################################################################################

CONST_FUNCAPP_PLAN=$1
CONST_LOCATION=$2
CONST_FUNCAPP_DOCKER_IMAGE=$3
CONNECTION_STRING=$4

if [ -z "$CONST_FUNCAPP_PLAN" ]
then
    CONST_FUNCAPP_PLAN=$CROP_RG_NAME'funcapppremiumplan'
fi

if [ -z "$CONST_LOCATION" ]
then
    CONST_LOCATION='uksouth'
fi

if [ -z "$CONST_FUNCAPP_DOCKER_IMAGE" ]
then
    CONST_FUNCAPP_DOCKER_IMAGE='turingcropapp/functions:dev'
fi

if [ -z "$CONNECTION_STRING" ]
then
    # Getting the first storage account key - this is a bit fragile in that it
    # depends on the order that the azure cli returns parameters
    ACCESS_KEY=$(az storage account keys list --account-name $CROP_STORAGE_ACCOUNT --resource-group $CROP_RG_NAME --output tsv |head -1 | awk '{print $4}')
    # Creating a connection string
    CONNECTION_STRING="DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;AccountName=${CROP_STORAGE_ACCOUNT};AccountKey=${ACCESS_KEY}"
fi

function_name=$CROP_RG_NAME"functionapp"
cwd=`pwd`

echo "CROP BUILD INFO: Function APP: cd ../../../__app__"
cd ../../../__app__

echo "CROP BUILD INFO: Function APP: az functionapp delete"
az functionapp delete \
    --name $function_name \
    --resource-group $CROP_RG_NAME \
    --subscription $CROP_SUBSCRIPTION_ID

echo "CROP BUILD INFO: Function APP: functionapp plan delete"
az functionapp plan delete \
    --resource-group $CROP_RG_NAME \
    --name $CONST_FUNCAPP_PLAN \
    --yes

echo "CROP BUILD INFO: Function APP: functionapp plan create"
az functionapp plan create \
    --resource-group $CROP_RG_NAME \
    --name $CONST_FUNCAPP_PLAN \
    --location $CONST_LOCATION \
    --number-of-workers 1 \
    --sku EP1 \
    --is-linux

echo "CROP BUILD INFO: Function APP: az functionapp create"

az functionapp create \
    --subscription $CROP_SUBSCRIPTION_ID \
    --resource-group $CROP_RG_NAME \
    --storage-account $CROP_STORAGE_ACCOUNT \
    --name $function_name \
    --functions-version 3 \
    --runtime python \
    --runtime-version 3.8 \
    --plan $CONST_FUNCAPP_PLAN \
    --deployment-container-image-name $CONST_FUNCAPP_DOCKER_IMAGE \
    --docker-registry-server-user $CROP_DOCKER_USER \
    --docker-registry-server-password $CROP_DOCKER_PASS

echo "CROP BUILD INFO: Function APP: $function_name created."

echo "CROP BUILD INFO: Function APP: sleeping for 30 seconds"
sleep 30

echo "CROP BUILD INFO: Function APP: az functionapp config appsettings set"

az functionapp config appsettings set \
    --name $function_name \
    --resource-group $CROP_RG_NAME \
    --settings "CROP_SQL_HOST=$CROP_SQL_HOST" \
    "CROP_SQL_SERVER=$CROP_SQL_SERVER" \
    "CROP_SQL_DBNAME=$CROP_SQL_DBNAME" \
    "CROP_SQL_USER=$CROP_SQL_USER" \
    "CROP_SQL_PASS=$CROP_SQL_PASS" \
    "CROP_SQL_PORT=$CROP_SQL_PORT" \
    "CROP_STARK_USERNAME=$CROP_STARK_USERNAME" \
    "CROP_STARK_PASS=$CROP_STARK_PASS" \
    "CROP_30MHZ_APIKEY=$CROP_30MHZ_APIKEY" \
    "CROP_30MHZ_TEST_T_RH_CHECKID=$CROP_30MHZ_TEST_T_RH_CHECKID" \
    "CROP_HYPER_APIKEY=$CROP_HYPER_APIKEY" \
    "CROP_OPENWEATHERMAP_APIKEY=$CROP_OPENWEATHERMAP_APIKEY" \
    "AzureWebJobsStorage=$CONNECTION_STRING" \
    > /dev/null

echo "CROP BUILD INFO: Function APP: $function_name configuration updated"

python $cwd/create_json.py $CONNECTION_STRING local.settings.json

echo "CROP BUILD INFO: Function APP: local.settings.json file updated."

echo "CROP BUILD INFO: Function APP: func azure functionapp publish"
func azure functionapp publish $function_name --build-native-deps --build remote

echo "CROP BUILD INFO: Function APP "$function" uploaded"

echo "CROP BUILD INFO: Function APP cd: "$cwd
cd $cwd
