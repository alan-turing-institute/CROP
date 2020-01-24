## Testing locally

- `cd croptriggers`
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

## Creating new function

- e.g. `func new --name advantixupload --template "Azure Blob Storage trigger"`
