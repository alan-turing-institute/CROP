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

    echo Group $AZURE_RG_NAME created.
fi

###################################################################################
# Creates STORAGE ACCOUNT
###################################################################################

# Checks if storage account does not exist

exist=`az storage account check-name --name $AZURE_STORAGE_ACCOUNT | python -c 'import json,sys;obj=json.load(sys.stdin);print (obj["nameAvailable"])'`

echo $exist

# az storage account create --name $AZURE_STORAGE_ACCOUNT \
#     --location $CONST_LOCATION \
#     --resource-group $AZURE_RG_NAME \
#     --sku Standard_LRS \

###################################################################################
# Creates CONTAINERS
###################################################################################

