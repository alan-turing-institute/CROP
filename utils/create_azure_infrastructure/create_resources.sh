#!/bin/bash

# CONSTANTS
CONST_LOCATION='uksouth'
CONST_POSTGRES_V='9.6'
CONST_POSTGRES_SERVER='B_Gen5_1'

# Declare an array of string with the names of containers
#   TODO: this probably needs to be extracted from the Python module
declare -a ContainersArray=("advantixrawdata" "advantixprocessed" "tinytagrawdata" "tinytagprocessed")

###################################################################################
# THE CODE BELOW SHOULD NOT BE MODIFIED
###################################################################################

# Setting the default subsciption
az account set -s $ARM_SUBSCRIPTION_ID

###################################################################################
# Creates RESOURCE GROUP
###################################################################################

# If resource group does not exist - create
if ! `az group exists -n $AZURE_RG_NAME`; then

    az group create --name $AZURE_RG_NAME \
        --location $CONST_LOCATION

    echo CROPINFO: Group $AZURE_RG_NAME has been created.
fi

###################################################################################
# Creates STORAGE ACCOUNT
###################################################################################

# Checks if storage account does not exist
#   This is not a great implementation as it depends on Python to parse the json object.
#   Changes are wellcome.
available=`az storage account check-name --name $AZURE_STORAGE_ACCOUNT | python -c 'import json,sys;obj=json.load(sys.stdin);print (obj["nameAvailable"])'`

if [ $available = "True" ]; then

    az storage account create --name $AZURE_STORAGE_ACCOUNT \
        --location $CONST_LOCATION \
        --resource-group $AZURE_RG_NAME \
        --sku Standard_LRS

    echo CROPINFO: Storage account $AZURE_STORAGE_ACCOUNT has been created.
fi

###################################################################################
# Creates BLOB CONTAINERS
###################################################################################

# Getting the access key
ACCESS_KEY=$(az storage account keys list --account-name $AZURE_STORAGE_ACCOUNT --resource-group $AZURE_RG_NAME --output tsv |head -1 | awk '{print $3}')

for container in ${ContainersArray[@]}; do

    # Checks if container exists
    #   This is not a great implementation as it depends on Python to parse the json object.
    #   Changes are wellcome.
    exists=$(az storage container exists --name $container --account-name $AZURE_STORAGE_ACCOUNT --account-key $ACCESS_KEY | python -c 'import json,sys;obj=json.load(sys.stdin);print (obj["exists"])')
   
    if ! $exists; then
        az storage container create \
            --name $container \
            --account-name $AZURE_STORAGE_ACCOUNT \
            --account-key $ACCESS_KEY

        echo CROPINFO: Container $container has been created.
    fi
done

###################################################################################
# Creates PostgreSQL DB
###################################################################################

# Checks for postgres databases
#   This is not a great implementation as it depends on Python to parse the json object.
#   Changes are wellcome.

exists=`az postgres server list -g $AZURE_RG_NAME`

if [ ${#exists} = 2 ]; then
    az postgres server create \
        --resource-group $AZURE_RG_NAME \
        --name $AZURE_SQL_SERVER \
        --location $CONST_LOCATION \
        --admin-user $AZURE_SQL_USER \
        --admin-password $AZURE_SQL_PASS \
        --sku-name $CONST_POSTGRES_SERVER \
        --version $CONST_POSTGRES_V

    echo CROPINFO: PostgreSQL DB $AZURE_SQL_SERVER has been created.

    # Adding rules of allowed ip addresses
    az postgres server firewall-rule create \
        --resource-group $AZURE_RG_NAME \
        --server-name $AZURE_SQL_SERVER \
        -n wifi \
        --start-ip-address  \
        --end-ip-address

    az postgres server firewall-rule create \
        --resource-group $AZURE_RG_NAME \
        --server-name $AZURE_SQL_SERVER \
        -n cable \
        --start-ip-address  \
        --end-ip-address

    echo CROPINFO: PostgreSQL DB firewall rules created.
fi

###################################################################################
# Creates Function App
###################################################################################

function='croptriggers'

cwd=`pwd`
cd ../$function

az functionapp create \
    --resource-group $AZURE_RG_NAME \
    --consumption-plan-location $CONST_LOCATION \
    --storage-account $AZURE_STORAGE_ACCOUNT \
    --name $function \
    --os-type Linux \
    --runtime python \
    --runtime-version 3.7

echo CROPINFO: Function APP $function created.

func azure functionapp publish $function --build-native-deps --build remote
cd $cwd

echo CROPINFO: Finished.