#!/bin/bash

# CONSTANTS
CONST_LOCATION='uksouth'
CONST_POSTGRES_V='11'
CONST_POSTGRES_SERVER='B_Gen5_1'
CONST_FUNCAPP_PLAN=$CROP_RG_NAME'funcapppremiumplan'
CONST_FUNCAPP_DOCKER_IMAGE='turingcropapp/webapp:funcapp'
CONST_WEBAPP_SKU='P1V2'

# Declare an array of string with the names of containers
# TODO: this probably needs to be extracted from the Python module
declare -a ContainersArray=("advanticsys-raw-data")

# az login

###################################################################################
# THE CODE BELOW SHOULD NOT BE MODIFIED
###################################################################################

# Setting the default subsciption
az account set -s $CROP_SUBSCRIPTION_ID
echo "CROP BUILD INFO: default subscription set to $CROP_SUBSCRIPTION_ID"

# ###################################################################################
# # Creates RESOURCE GROUP
# ###################################################################################

# # If resource group does not exist - create
# if ! `az group exists -n $CROP_RG_NAME`; then

#     az group create --name $CROP_RG_NAME \
#         --location $CONST_LOCATION

#     echo "CROP BUILD INFO: resource group $CROP_RG_NAME has been created."
# else
#     echo "CROP BUILD INFO: resource group $CROP_RG_NAME already exists. Skipping."
# fi

# ###################################################################################
# # Creates STORAGE ACCOUNT
# ###################################################################################

# # Checks if storage account does not exist
# #   This is not a great implementation as it depends on Python to parse the json object.
# #   Changes are wellcome.
# available=`az storage account check-name --name $CROP_STORAGE_ACCOUNT | python -c 'import json,sys;obj=json.load(sys.stdin);print (obj["nameAvailable"])'`

# if [ $available = "True" ]; then

#     az storage account create --name $CROP_STORAGE_ACCOUNT \
#         --location $CONST_LOCATION \
#         --resource-group $CROP_RG_NAME \
#         --sku Standard_LRS

#     echo "CROP BUILD INFO: storage account $CROP_STORAGE_ACCOUNT has been created."
# else
#     echo "CROP BUILD INFO: storage account $CROP_STORAGE_ACCOUNT already exists. Skipping."
# fi

# # Getting the first storage account key
# ACCESS_KEY=$(az storage account keys list --account-name $CROP_STORAGE_ACCOUNT --resource-group $CROP_RG_NAME --output tsv |head -1 | awk '{print $3}')
# # Creating a connection string
# CONNECTION_STRING="DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;AccountName=${CROP_STORAGE_ACCOUNT};AccountKey=${ACCESS_KEY}"

# ###################################################################################
# # Creates BLOB CONTAINERS
# ###################################################################################

# for container in ${ContainersArray[@]}; do

#     # Checks if container exists
#     #   This is not a great implementation as it depends on Python to parse the json object.
#     #   Changes are wellcome.
#     exists=$(az storage container exists --name $container --account-name $CROP_STORAGE_ACCOUNT --account-key $ACCESS_KEY | python -c 'import json,sys;obj=json.load(sys.stdin);print (obj["exists"])')

#     if ! $exists; then
#         az storage container create \
#             --name $container \
#             --account-name $CROP_STORAGE_ACCOUNT \
#             --account-key $ACCESS_KEY

#         echo "CROP BUILD INFO: Container $container has been created."
#     else
#         echo "CROP BUILD INFO: Container $container already exists. Skipping."
#     fi
# done

# ###################################################################################
# # Creates PostgreSQL DB
# ###################################################################################

# # Checks for postgres databases
# #   This is not a great implementation as it depends on Python to parse the json object.
# #   Changes are wellcome.

# exists=`az postgres server list -g $CROP_RG_NAME`

# # Checks the lenght of the query result. 2 means there were no results.
# if [ ${#exists} = 2 ]; then
#     az postgres server create \
#         --resource-group $CROP_RG_NAME \
#         --name $CROP_SQL_SERVER \
#         --location $CONST_LOCATION \
#         --admin-user $CROP_SQL_USERNAME \
#         --admin-password $CROP_SQL_PASS \
#         --sku-name $CONST_POSTGRES_SERVER \
#         --version $CONST_POSTGRES_V \
#         --ssl-enforcement Disabled

#     echo "CROP BUILD INFO: PostgreSQL DB $CROP_SQL_SERVER has been created."

#     # Adding rules of allowed ip addresses
#     declare -a IPArray=($CROP_SQL_WHITEIPS)

#     for ip in ${IPArray[@]}; do

#         az postgres server firewall-rule create \
#             --resource-group $CROP_RG_NAME \
#             --server-name $CROP_SQL_SERVER \
#             -n whitelistedip \
#             --start-ip-address $ip \
#             --end-ip-address $ip
#     done

#     echo "CROP BUILD INFO: PostgreSQL DB $CROP_SQL_SERVER firewall rules created."
      
#     read -n 1 -s -r -p "CROP BUILD INFO: Reminder: do not forget to allow access to Azure services for the SQL database"
#     # allow access to Azure services as YES
# else
#     echo "CROP BUILD INFO: PostgreSQL DB $CROP_SQL_SERVER already exists. Skipping."
# fi

###################################################################################
# Creates Function App
###################################################################################

function_name=$CROP_RG_NAME"functionapp"
cwd=`pwd`

echo "CROP BUILD INFO: Function APP: cd ../../__app__"
cd ../../__app__

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
    --functions-version 2 \
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
    > /dev/null

echo "CROP BUILD INFO: Function APP: $function_name configuration updated"

python $cwd/create_json.py $CONNECTION_STRING local.settings.json

echo "CROP BUILD INFO: Function APP: local.settings.json file updated."

echo "CROP BUILD INFO: Function APP: func azure functionapp publish"
func azure functionapp publish $function_name --build-native-deps --build remote

echo "CROP BUILD INFO: Function APP "$function" uploaded"

echo "CROP BUILD INFO: Function APP cd: "$cwd
cd $cwd

# ###################################################################################
# # Creates WebApp
# ###################################################################################

# webapp_appservice_name=$CROP_RG_NAME"webappservice"
# webapp_name=$CROP_RG_NAME

# echo "CROP BUILD INFO: WebApp: az webapp delete"

# az webapp delete \
#     --name $webapp_name \
#     --resource-group $CROP_RG_NAME \
#     --subscription $CROP_SUBSCRIPTION_ID

# echo "CROP BUILD INFO: WebApp: az appservice plan delete"

# az appservice plan delete \
#     --name $webapp_appservice_name \
#     --resource-group $CROP_RG_NAME \
#     --subscription $CROP_SUBSCRIPTION_ID \
#     --yes

# echo "CROP BUILD INFO: WebApp: az appservice plan create"

# az appservice plan create \
#     --name $webapp_appservice_name \
#     --resource-group $CROP_RG_NAME \
#     --is-linux \
#     --location $CONST_LOCATION \
#     --number-of-workers 1 \
#     --sku $CONST_WEBAPP_SKU \
#     --subscription $CROP_SUBSCRIPTION_ID

# echo "CROP BUILD INFO: WebApp: az webapp create"

# az webapp create \
#     --name $webapp_name \
#     --plan $webapp_appservice_name \
#     --resource-group $CROP_RG_NAME \
#     --deployment-container-image-name turingcropapp/webapp:$CROP_RG_NAME \
#     --docker-registry-server-password $CROP_DOCKER_PASS \
#     --docker-registry-server-user $CROP_DOCKER_USER \
#     --subscription $CROP_SUBSCRIPTION_ID

# read -n 1 -s -r -p "CROP BUILD INFO: Reminder: do not forget to activate Continuous Deployment for the container and update the webhook on docker hub"
# echo ""

# ###################################################################################

echo "CROP BUILD INFO: Finished."

