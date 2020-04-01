# Steps to create Azure infrastructure

0. Prerequisites

  - install latest version of Python3 and pip3
  - install dependencies
    `pip install -r ../../core/requirements.txt`

1. Create Azure resources

  - Modify `../../.secrets/crop.sh`
  - Modify `create_resources.sh`
    - Check settings
    - Add IP addresses to whitelist (Future)
  - Execute from the command line
    ```{bash}
    source ../../.secrets/crop.sh ; ./create_resources.sh
    ```

2. Create PostgreSQL DB
  
  - Execute from the command line

    ```
    source ../../.secrets/crop.sh ; python create_db.py
    ```
