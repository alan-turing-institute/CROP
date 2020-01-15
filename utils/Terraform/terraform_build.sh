#!/bin/sh

echo "Setting environment variables for Terraform and CROP"
source .secrets/azure.sh
az account set --subscription="${ARM_SUBSCRIPTION_ID}"

echo "Initialising Terraform"
# This step downloads the Azure modules required to create an Azure resource group.
terraform init

echo "Authenticate Terraform using Azure CLI"
terraform apply
