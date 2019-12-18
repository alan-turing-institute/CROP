## upload_sensor_data.sh

A script to upload data to Azure blob storage.

**Usage**

upload_sensor_data.sh (full path to the file to be uploaded) (unique blob name)

**Example**
```
./upload_sensor_data.sh ../tests/data/Advantix/data-20190821-test1.csv 20190821-test1.csv
```

Expects

.secrets/azure_auth.sh file to be sourced.

Requirements:

python >= 3.7.4
requirements.txt

Python3 dependencies can be installed using pip:
```
pip3 install -r requirements.txt
```
