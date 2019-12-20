import logging

import azure.functions as func


def main(blobin: func.InputStream):
    logging.info(f"Python blob trigger function processed blob \n"
                 f"Name: {blobin.name}\n"
                 f"Blob Size: {blobin.length} bytes")

    ######
    ### Place holder for data ingress processess
    ######
