## Testing locally

- `cd croptriggers`
- Modify `local.settings.json`

```json
{
  "IsEncrypted": false,
  "Values": {
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AzureWebJobsStorage": "",
    "CROP_SQL_SERVER": "", 
    "CROP_SQL_USER": "", 
    "CROP_SQL_PORT": "", 
    "CROP_SQL_PASS": "", 
    "CROP_SQL_DBNAME": ""
  }
}
```

`AzureWebJobsStorage` - Function app -> Configuration -> AzureWebJobsStorage
<!-- `MyStorageConnectionString` - copy from storage->Access keys->Connection string -->

- `func start`

## Creating a new function

- e.g. `func new --name advanticsys --template "Azure Blob Storage trigger"`


## References:

- [Blob trigger example](https://github.com/yokawasa/azure-functions-python-samples/tree/master/v2functions/blob-trigger-watermark-blob-out-binding)