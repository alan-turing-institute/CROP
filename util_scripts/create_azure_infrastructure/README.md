# OUT OF DATE
The scripts in this folder are out of date as of 2022-08-31. They need to be updated or removed. Using them might mess up your deployment.

# CROP infrastructure

**Azure** cloud platform is used to host the CROP infrastructure, i.e. webapp, storage, serverless applications. The creation of the infrastructure is an automated process that can be performed by following few simple steps outlined below.

### Step 0. Prerequisites
  - Azure subscription to host the infrastructure
  - Latest versions of Python (3.7 or greater) and pip
  - Installed Python dependencies

    `pip install -r ../../requirements.txt`

  - Created and configured environmental parameters file (`../../.secrets/crop.sh`). Template for reference: `../../.secrets/template_crop.sh`

### Step 1. Create Azure infrastructure

  - Navigate to _utils/create_azure_infrastructure_ directory:
    ```{bash}
    cd CROP/utils/create_azure_infrastructure`
    ```
  - Read and execute environmental parameters file:
    ```{bash}
    source ../../.secrets/crop.sh`
    ```
  - Execute the infrastructure creation script:
    ```{bash}
    ./create_resources.sh
    ```
    The script will:
      - create (if it doesn't exist):
        - Resource group
        - Storage account (if it doesn't exist)
        - Storage containers (if they don't exist)
        - PostgreSQL DB (if it doesn't exist)
        - Function apps (if they don't exist)
      - Update:
        - Function app configuration
        - local.settings.json
      - Upload:
        - Function app

### Step 2. Initialise DB

  - Execute the database initialisation script and type "Y"

    ```{bash}
    python initialise_db.py
    ```
