# Manual (Azure)

## 1. Resource group

Resource groups provide a way to monitor, control access, provision and manage billing for collections of assets that are required to run an application, or used by a client or company department.

We start by creating a new resource group under our Azure subscription:

**Dashboard->Resource groups->Create a resource group:**

```
Subscription: Urban Agriculture
Resource group: CROP
Region: (Europe) UK South
```

## 2. SQL database

**Dashboard->New->Marketplace->Azure Database for PostgreSQL**

```
Choose: Single server

Project details:
  Subscription: Urban Agriculture
  Resource group: CROP

Server details:
  Server name: cropserver
  Data source: None
  Admin username: <>
  Password: <>
  Location: (Europe) UK South
  Version: 10
  Compute + storage: Basic 1vCores, 5GB storage


Added Turing IP address.

```

## Storage account

**Dashboard->Storage accounts->Create storage account**

```
Project details
  Subscription: Urban Agriculture
  Resource group: CROP

Instance details
  Storage account name: cropstoragetest
  Location: (Europe) UK South
  Performance: Standard
  Account kind: Storage (general purpose v1)
  Replication: LRS

Network connectivity
  Connectivity method: Public endpoint (all networks)

```

**Dashboard->cropstoragetest - Containers +**
```
Name: sensordata
Public access level: Private
```

**Dashboard->cropstoragetest - Shared access signature**

```
Allowed services: Blob
Allowed resource types: Container, Object
Allowed permissions: List, Create
Start: 01/02/2020
End: 01/02/2021
```


# Prototype Cloud infrastructure (Azure / Terraform)

Requirements:
- An active Microsoft Azure subscription with at least $100 budget.
- Terraform (https://www.terraform.io/downloads.html)
- Azure CLI


## 0. Set up (MacOS)

Get the subscription and tenant IDs for the Azure subscription that will be used to build the infrastructure.

```
az account list --query "[].{name:name, subscriptionId:id, tenantId:tenantId}"
```

Then modify/create `.secrets/azure.sh` which should like like this, where the values for `AZURE_SUBSCRIPTION_ID` and `AZURE_TENANT_ID` should be taken from the previous commands output.

```
echo "Setting environment variables for Terraform and CROP"
export ARM_SUBSCRIPTION_ID="00000000-0000-0000-0000-000000000000"
export ARM_TENANT_ID="11111111-1111-1111-1111-111111111111"
```

Then execute:

```
cd CROP

./terraform_build.sh
```
