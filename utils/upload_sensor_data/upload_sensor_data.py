#!/usr/bin/python

"""
A script to uploads a file as a blob to a container in Azure storage account.
"""

import argparse
from azure.storage.blob import BlockBlobService


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
    parser = argparse.ArgumentParser(
        description="Uploads a file as a blob to a container in Azure storage account."
    )

    parser.add_argument("storageacc", default=None, help="Storage account name.")
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

    #args = parser.parse_args()
    args, unknown = parser.parse_known_args()

    file_path = (args.source).strip()
    blob_name = (args.target).strip()

    # connects to the storage account's blob service using the connection string
    blob_service = BlockBlobService(
        account_name=args.storageacc, connection_string=args.connectionstr
    )

    # checks if blob already exists
    blob_exists = check_blob_exists(blob_service, args.container, blob_name)

    if not blob_exists:
        try:
            # uploads a new blob
            blob_service.create_blob_from_path(args.container, blob_name, file_path)
        except ValueError as error:
            raise RuntimeError(error)
    else:
        raise RuntimeError("Blob named %s already exists!" % (blob_name))

    print("Success.")
