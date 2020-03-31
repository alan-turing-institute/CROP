#!/bin/bash

# CONSTANTS
CONST_LOCATION='uksouth'
CONST_POSTGRES_V='9.6'
CONST_POSTGRES_SERVER='B_Gen5_1'

# Declare an array of string with the names of containers
# TODO: this probably needs to be extracted from the Python module
declare -a ContainersArray=("advanticsys-raw-data" "advanticsys-processed-data") 

# ###################################################################################
# # THE CODE BELOW SHOULD NOT BE MODIFIED
# ###################################################################################

# # az login

# # Setting the default subsciption
# az account set -s $CROP_SUBSCRIPTION_ID

# ###################################################################################
# # Creates RESOURCE GROUP
# ###################################################################################

# # If resource group does not exist - create
# if ! `az group exists -n $CROP_RG_NAME`; then

#     az group create --name $CROP_RG_NAME \
#         --location $CONST_LOCATION

#     echo CROP BUILD INFO: Group $CROP_RG_NAME has been created.
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

#     echo CROP BUILD INFO: Storage account $CROP_STORAGE_ACCOUNT has been created.
# fi

# # Getting the first storage account key
# ACCESS_KEY=$(az storage account keys list --account-name $CROP_STORAGE_ACCOUNT --resource-group $CROP_RG_NAME --output tsv |head -1 | awk '{print $3}')
# # Creating a connection string
# CONNECTION_STRING="DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;AccountName=${CROP_STORAGE_ACCOUNT};AccountKey=${ACCESS_KEY}"

# ###################################################################################
# # Creates BLOB CONTAINERS
# ###################################################################################

# # Getting the access key
# ACCESS_KEY=$(az storage account keys list --account-name $CROP_STORAGE_ACCOUNT --resource-group $CROP_RG_NAME --output tsv |head -1 | awk '{print $3}')

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

#         echo CROP BUILD INFO: Container $container has been created.
#     fi
# done

# ###################################################################################
# # Creates PostgreSQL DB
# ###################################################################################

# # Checks for postgres databases
# #   This is not a great implementation as it depends on Python to parse the json object.
# #   Changes are wellcome.

# exists=`az postgres server list -g $CROP_RG_NAME`

# if [ ${#exists} = 2 ]; then
#     az postgres server create \
#         --resource-group $CROP_RG_NAME \
#         --name $CROP_SQL_SERVER \
#         --location $CONST_LOCATION \
#         --admin-user $CROP_SQL_USERNAME \
#         --admin-password $CROP_SQL_PASS \
#         --sku-name $CONST_POSTGRES_SERVER \
#         --version $CONST_POSTGRES_V

#     echo CROP BUILD INFO: PostgreSQL DB $CROP_SQL_SERVER has been created.

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

#     echo CROP BUILD INFO: PostgreSQL DB firewall rules created.
# fi

###################################################################################
# Creates Function App
###################################################################################

function_name='croptriggers'

cwd=`pwd`
cd ../$function_name

az functionapp create \
    --resource-group $CROP_RG_NAME \
    --consumption-plan-location $CONST_LOCATION \
    --storage-account $CROP_STORAGE_ACCOUNT \
    --name $CROP_RG_NAME"functionapp" \
    --os-type Linux \
    --runtime python \
    --runtime-version 3.7 \
    --functions-version 2

az functionapp config appsettings set \
    --name $CROP_RG_NAME"functionapp" \
    --resource-group $CROP_RG_NAME \
    --settings "CROP_SQL_SERVER=$CROP_SQL_SERVER" \
    "CROP_SQL_DBNAME=$CROP_SQL_DBNAME" \
    "CROP_SQL_USER=$CROP_SQL_USER" \
    "CROP_SQL_PASS=$CROP_SQL_PASS" \
    "CROP_SQL_PORT=$CROP_SQL_PORT"
    
echo CROP BUILD INFO: Function APP $function created.

# creating the utils/croptrigger/local.settings.json file
python ../create_azure_infrastructure/create_json.py $CONNECTION_STRING local.settings.json

func azure functionapp publish $function --build-native-deps --build remote
cd $cwd

echo CROP BUILD INFO: Function APP $function uploaded.

echo CROP BUILD INFO: Finished.
