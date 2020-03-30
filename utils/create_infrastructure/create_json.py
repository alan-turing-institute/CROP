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
        "CROP_SQL_SERVER": os.environ["CROP_SQL_SERVER"],
        "CROP_SQL_USER": os.environ["CROP_SQL_USER"],
        "CROP_SQL_PASS": os.environ["CROP_SQL_PASS"],
        "CROP_SQL_DBNAME": os.environ["CROP_SQL_DBNAME"],
        "CROP_SQL_PORT": os.environ["CROP_SQL_PORT"]
    }

    with open(rel_file_path, 'w') as outfile:
        json.dump(data, outfile)
    
    print("Finished.")