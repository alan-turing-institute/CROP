#!/bin/bash

# CONSTANTS
CONST_LOCATION='uksouth'

# Setting the default subsciption
az account set -s $ARM_SUBSCRIPTION_ID

###################################################################################
# Creates RESOURCE GROUP
###################################################################################

# If resource group does not exist - create
if ! `az group exists -n $AZURE_RG_NAME`; then

    az group create --name $AZURE_RG_NAME \
        --location $CONST_LOCATION \
        > /dev/null 2>&1

    echo Group $AZURE_RG_NAME has been created.
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
        --sku Standard_LRS \
        > /dev/null 2>&1

    echo Storage account $AZURE_STORAGE_ACCOUNT has been created.
fi

###################################################################################
# Creates BLOB CONTAINERS
###################################################################################

# Getting the access key
ACCESS_KEY=$(az storage account keys list --account-name $AZURE_STORAGE_ACCOUNT --resource-group $AZURE_RG_NAME --output tsv |head -1 | awk '{print $3}')

# Declare an array of string with the names of containers
#   TODO: this probably needs to be extracted from the Python module
declare -a ContainersArray=("advantixrawdata" "tinytagrawdata")

for container in ${ContainersArray[@]}; do

    # Checks if container exists
    #   This is not a great implementation as it depends on Python to parse the json object.
    #   Changes are wellcome.
    exists=$(az storage container exists --name $container --account-name $AZURE_STORAGE_ACCOUNT --account-key $ACCESS_KEY | python -c 'import json,sys;obj=json.load(sys.stdin);print (obj["exists"])')
   
    if ! $exists; then
        az storage container create  \
            --name $container \
            --account-name $AZURE_STORAGE_ACCOUNT \
            --account-key $ACCESS_KEY \
            > /dev/null 2>&1

        echo Container $container has been created.
    fi
done