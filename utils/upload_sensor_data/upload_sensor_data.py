#!/usr/bin/python

"""
Script to upload data to Azure blob storage.

"""

import os
import argparse
from azure.storage.blob import BlockBlobService, PublicAccess

def check_blob_exists(block_blob_service, container_name, blob_name):
    """
    Checks if blob with name blob_name exists

    Args:
        block_blob_service - block blob service object
        container_name - container's name
        blob_name - blob's name
    Returns:
        True if blob already exists, otherwise False.
    """

    exist = False

    generator = block_blob_service.list_blobs(container_name)

    for blob in generator:
        if blob.name == blob_name:
            exist = True
            break

    return exist

if __name__ == "__main__":

    # Command line arguments
    parser = argparse.ArgumentParser(description="Uploads blobs to Azure")

    parser.add_argument("--source", default=None, help="Full path to the file to be uploaded")
    parser.add_argument("--target", default=None, help="A unique target (blob) name")
    args = parser.parse_args()

    if not args.source or not args.target:
        raise RuntimeError("Source file and/or target name were not specified.")

    try:
        az_account = os.environ['AZURE_STORAGE_ACCOUNT']
        az_container = os.environ['AZURE_CONTAINER']
        az_connect_str = os.environ['AZURE_CONNECTION_STRING']
    except:
        raise RuntimeError("Cannot read azure storage account settings.")

    file_path = (args.source).strip()
    blob_name = (args.target).strip()

    # connect's to the storage account's blob service using the connection string
    blob_service = BlockBlobService(account_name=az_account, connection_string=az_connect_str)

    # checks if blob already exists
    blob_exists = check_blob_exists(blob_service, az_container, blob_name)
    if not blob_exists:
        try:
            # uploads a new blob
            blob_service.create_blob_from_path(az_container, blob_name, file_path)
        except ValueError as error:
            raise RuntimeError(error)
    else:
        raise RuntimeError("Blob named %s already exists!" % (blob_name))

    print("Finised.")
