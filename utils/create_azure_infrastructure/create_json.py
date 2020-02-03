import json
import sys
import os

"""
Creates local.settings.json file for Azure Function App
"""

if __name__ == "__main__":

    conn_string = sys.argv[1].strip()
    rel_file_path = sys.argv[2].strip()

    data = {}

    data["IsEncrypted"] = "false"
    data["Values"] = {
        "FUNCTIONS_WORKER_RUNTIME": "python",
        "AzureWebJobsStorage": conn_string,
        "AZURE_SQL_SERVER": os.environ["AZURE_SQL_SERVER"],
        "AZURE_SQL_USER": os.environ["AZURE_SQL_USER"],
        "AZURE_SQL_PASS": os.environ["AZURE_SQL_PASS"],
        "AZURE_SQL_DBNAME": os.environ["AZURE_SQL_DBNAME"],
        "AZURE_SQL_PORT": os.environ["AZURE_SQL_PORT"]
    }

    with open(rel_file_path, 'w') as outfile:
        json.dump(data, outfile)
    
    print("Finished.")