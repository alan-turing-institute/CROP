import os
import requests
import json

CROP_30MHZ_ORG = os.environ["CROP_30MHZ_ORGANIZATION"].strip()
CROP_30MHZ_APIKEY = os.environ["CROP_30MHZ_APIKEY"].strip()

def main():
    """
    Main test routine

    """

    test_check()

    test_data_export()

def test_check():

    success = True
    error = ""
    content = None

    url = 'https://api.30mhz.com/api/check/organization/' + CROP_30MHZ_ORG

    headers = {
        'Content-Type': 'application/json',
        'Authorization': CROP_30MHZ_APIKEY,
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        content = json.loads(response.content)
    else:
        error = "Request's [%s] status code: %d" % (url, response.status_code)
        success = False

    assert success, error

    # print(len(content))

    # for i, val in enumerate(content):
    #     print(i, val)

def test_data_export():

    success = True
    error = ""
    content = None

    url = 'https://api.30mhz.com/api/data-export/organization/' + CROP_30MHZ_ORG

    headers = {
        'Content-Type': 'application/json',
        'Authorization': CROP_30MHZ_APIKEY,
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        content = json.loads(response.content)
    else:
        error = "Request's [%s] status code: %d" % (url, response.status_code)
        success = False

    assert success, error

    # print(len(content))
    # print(content)


if __name__ == "__main__":

    main()