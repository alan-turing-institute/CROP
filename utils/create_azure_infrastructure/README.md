# Steps to create Azure infrastructure

0. Prerequisites

  - install latest version of Python3 and pip3
  - `pip3 install -r ../../requirements.txt`

1. Create Azure resources

  - Modify `../../.secrets/azure.sh`
  - Modify `create_resources.sh`
    - Add IP addresses to whitelist
    - Check settings
  - Execute from the command line
    ```{bash}
    source ../../.secrets/azure.sh ; ./create_resources.sh
    ```

2. Create PostgreSQL DB
  
  - Execute from the command line

    ```
    source ../../.secrets/azure.sh ; python3 create_db.py
    ```
