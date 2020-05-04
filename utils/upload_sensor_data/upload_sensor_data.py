#!/usr/bin/python

"""
A script to uploads a file as a blob to a container in Azure storage account.
"""

import argparse
from azure.storage.blob import BlobServiceClient


if __name__ == "__main__":

    # Command line arguments
    parser = argparse.ArgumentParser(
        description="Uploads a file as a blob to a container in Azure storage account."
    )

    parser.add_argument(
        "container",
        default=None,
        help="Container name (each sensor type has its own container).",
    )
    parser.add_argument(
        "connectionstr",
        default=None,
        help="Connection string with write and list permissions.",
    )
    parser.add_argument(
        "source", default=None, help="Full path to the file to be uploaded."
    )
    parser.add_argument("target", default=None, help="A unique target (blob) name.")

    args, unknown = parser.parse_known_args()

    container = args.container.strip()
    conn_str = args.connectionstr.strip()
    file_path = args.source.strip()

    blob_name = args.target.strip()

    blob_service_client = BlobServiceClient.from_connection_string(conn_str=conn_str)
    blob_client = blob_service_client.get_blob_client(
        container=container, blob=blob_name
    )

    try:
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

    except ValueError as error:
        raise RuntimeError(error)

    print("Success.")
