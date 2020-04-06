# upload_sensor_data.py

Script to upload sensor data to Azure blob storage.

**Depends on**:
  - Python >= 3.7.5
  - Python3 modules listed in `requirements.txt`.

Python3 dependencies can be installed using pip3:
```
pip3 install -r requirements.txt
```

### Usage

```
Uploads a file as a blob to a container in Azure storage account.

positional arguments:
  storageacc     Storage account name.
  container      Container name (each sensor type has its own container).
  connectionstr  Connection string with write and list permissions.
  source         Full path to the file to be uploaded.
  target         A unique target (blob) name.

optional arguments:
  -h, --help     show this help message and exit
```

Returns "Success" if the upload was successful, otherwise raises a RuntimeError.

### Example
```
python upload_sensor_data.py \
  --storageacc teststorageacc \
  --container testcontainer \
  --connectionstr "BlobEndpoint=..." \
  --source ../../core/tests/data/Advanticsys/data-20190821-test1.csv \
  --target 20190821-test1.csv
```

### Generating SAS and the connection string

- **Allowed services:** Blob
- **Allowed resource types:** Container, Object
- **Allowed permissions:** Write, List
- **Start:** 03/16/2020 2:57:28 PM
- **End:** 03/16/2022 2:57:28 PM
- **Allowed protocols:** HTTPS only
- **Signing key:** key1/key2
