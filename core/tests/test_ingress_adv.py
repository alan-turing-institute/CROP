"""
Test ingress.py module
"""

import os

from crop.constants import (
    CONST_TEST_DIR_DATA,
    CONST_ADVANTICSYS_FOLDER,
    CONST_ADVANTICSYS_TEST_1,
    CONST_ADVANTICSYS_TEST_2,
    CONST_ADVANTICSYS_TEST_3,
    CONST_ADVANTICSYS_TEST_4,
    CONST_ADVANTICSYS_TEST_5,
    CONST_ADVANTICSYS_TEST_6,
    CONST_ADVANTICSYS_TEST_7,
    CONST_ADVANTICSYS_TEST_8,
    CONST_ADVANTICSYS_TEST_9,
    ERR_IMPORT_ERROR_3,
)

from crop.ingress_adv import (
    advanticsys_read_csv,
    advanticsys_check_structure,
    advanticsys_import,
    advanticsys_convert,
    advanticsys_df_validity,
)


def test_advanticsys_read_csv():

    file_path = os.path.join(
        CONST_TEST_DIR_DATA, CONST_ADVANTICSYS_FOLDER, CONST_ADVANTICSYS_TEST_1
    )
    data_df = advanticsys_read_csv(file_path)
    # counting the number of entries
    assert len(data_df.index) == 75


def test_advanticsys_check_structure():

    # checks healthy data file
    file_path = os.path.join(
        CONST_TEST_DIR_DATA, CONST_ADVANTICSYS_FOLDER, CONST_ADVANTICSYS_TEST_1
    )
    data_df = advanticsys_read_csv(file_path)
    success, _ = advanticsys_check_structure(data_df)
    assert True == success

    # checks if data with mispelled column fails
    file_path = os.path.join(
        CONST_TEST_DIR_DATA, CONST_ADVANTICSYS_FOLDER, CONST_ADVANTICSYS_TEST_2
    )
    data_df = advanticsys_read_csv(file_path)
    success, _ = advanticsys_check_structure(data_df)
    assert False == success


def test_advanticsys_convert():

    # Good data
    file_path = os.path.join(
        CONST_TEST_DIR_DATA, CONST_ADVANTICSYS_FOLDER, CONST_ADVANTICSYS_TEST_1
    )
    data_df = advanticsys_read_csv(file_path)
    success, _, data_df = advanticsys_convert(data_df)
    assert True == success

    # One column is misppeled, the checks should pick this up and return None
    file_path = os.path.join(
        CONST_TEST_DIR_DATA, CONST_ADVANTICSYS_FOLDER, CONST_ADVANTICSYS_TEST_2
    )
    data_df = advanticsys_read_csv(file_path)
    success, _, data_df = advanticsys_convert(data_df)
    assert False == success
    assert None == data_df

    # Timestamp is wrong, the checks should return None
    file_path = os.path.join(
        CONST_TEST_DIR_DATA, CONST_ADVANTICSYS_FOLDER, CONST_ADVANTICSYS_TEST_3
    )
    data_df = advanticsys_read_csv(file_path)
    success, _, data_df = advanticsys_convert(data_df)
    assert False == success
    assert None == data_df

    # Modbus ID is wrong
    file_path = os.path.join(
        CONST_TEST_DIR_DATA, CONST_ADVANTICSYS_FOLDER, CONST_ADVANTICSYS_TEST_4
    )
    data_df = advanticsys_read_csv(file_path)
    success, _, data_df = advanticsys_convert(data_df)
    assert False == success

    # Temperature values are wrong
    file_path = os.path.join(
        CONST_TEST_DIR_DATA, CONST_ADVANTICSYS_FOLDER, CONST_ADVANTICSYS_TEST_5
    )
    data_df = advanticsys_read_csv(file_path)
    success, _, data_df = advanticsys_convert(data_df)
    assert False == success

    # Humidity values are wrong
    file_path = os.path.join(
        CONST_TEST_DIR_DATA, CONST_ADVANTICSYS_FOLDER, CONST_ADVANTICSYS_TEST_6
    )
    data_df = advanticsys_read_csv(file_path)
    success, _, data_df = advanticsys_convert(data_df)
    assert False == success

    # Co2 values are wrong
    file_path = os.path.join(
        CONST_TEST_DIR_DATA, CONST_ADVANTICSYS_FOLDER, CONST_ADVANTICSYS_TEST_7
    )
    data_df = advanticsys_read_csv(file_path)
    success, _, data_df = advanticsys_convert(data_df)
    assert False == success

    # Temp and humidity empty values, assert error 3
    file_path = os.path.join(
        CONST_TEST_DIR_DATA, CONST_ADVANTICSYS_FOLDER, CONST_ADVANTICSYS_TEST_8
    )
    data_df = advanticsys_read_csv(file_path)
    success, log, _ = advanticsys_convert(data_df)
    assert False == success
    assert ERR_IMPORT_ERROR_3 == log


def test_advanticsys_import():

    # One column is misppeled, the checks should pick this up and return None
    file_path = os.path.join(
        CONST_TEST_DIR_DATA, CONST_ADVANTICSYS_FOLDER, CONST_ADVANTICSYS_TEST_2
    )
    success, _, data_df = advanticsys_import(file_path)
    assert False == success
    assert None == data_df

    file_path = os.path.join(
        CONST_TEST_DIR_DATA, CONST_ADVANTICSYS_FOLDER, CONST_ADVANTICSYS_TEST_1
    )
    success, _, data_df = advanticsys_import(file_path)

    # counting the number of entries
    assert len(data_df.index) == 75


def test_advanticsys_df_validity():

    # Duplicate values test
    file_path = os.path.join(
        CONST_TEST_DIR_DATA, CONST_ADVANTICSYS_FOLDER, CONST_ADVANTICSYS_TEST_9
    )
    data_df = advanticsys_read_csv(file_path)

    success, _, data_df = advanticsys_convert(data_df)
    assert success

    success, _ = advanticsys_df_validity(data_df)
    assert False == success

    file_path = os.path.join(
        CONST_TEST_DIR_DATA, CONST_ADVANTICSYS_FOLDER, CONST_ADVANTICSYS_TEST_1
    )
    data_df = advanticsys_read_csv(file_path)

    success, _, data_df = advanticsys_convert(data_df)
    assert success

    success, log = advanticsys_df_validity(data_df)
    assert True == success, log
