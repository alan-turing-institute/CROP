# upload_sensor_data.sh

Script to upload sensor data to Azure blob storage.

**Depends on**:
  - Python >= 3.7.4
  - Python3 modules listed in `requirements.txt`.

Python3 dependencies can be installed using pip3:
```
pip3 install -r requirements.txt
```

**Expects**:
  Environmental parameters which can be sourced from `.secrets/azure.sh`

  `azure_template.sh` is a template for the `.secrets/azure.sh`

**Usage**

```
./upload_sensor_data.sh <full path to the file to be uploaded> <unique blob name>
```

**Example**
```
./upload_sensor_data.sh ../tests/data/Advantix/data-20190821-test1.csv 20190821-test1.csv
```
