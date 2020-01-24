## Testing locally

The example is written around the advantix sensor data upload function app, however, it could be used as a reference for other functions.

- `cd advantixupload`
- Modify `local.settings.json`

```json
{
  "IsEncrypted": false,
  "Values": {
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AzureWebJobsStorage": "",
    "MyStorageConnectionString": ""
  }
}
```

`AzureWebJobsStorage` - Function app -> Configuration -> AzureWebJobsStorage
`MyStorageConnectionString` - copy from storage->Access keys->Connection string

- `func start`