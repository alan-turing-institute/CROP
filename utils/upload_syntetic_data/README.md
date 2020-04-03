# upload_sensor_data.py

Script to upload syntetic data to a database.

**Depends on**:
  - Python >= 3.7.5
  - CROP package and its dependencies.

### Usage

```
usage: upload_syntetic_data.py [-h] dbname

Uploads syntetic data to a PostgreSQL database.

positional arguments:
  dbname      Database name

optional arguments:
  -h, --help  show this help message and exit

```

Returns "Success" if the upload was successful, otherwise raises a RuntimeError.

### Example
```
python upload_syntetic_data.py temp_db
```
