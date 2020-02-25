"""
Test ingress.py module
"""

import os
import sys
import pytest

from crop.constants import (
    CONST_TEST_DIR_DATA,
    CONST_ADVANTIX_FOLDER,
    CONST_ADVANTIX_TEST_1,
    CONST_ADVANTIX_TEST_2,
    CONST_ADVANTIX_TEST_3,
    CONST_ADVANTIX_TEST_4,
    CONST_ADVANTIX_TEST_5,
    CONST_ADVANTIX_TEST_6,
    CONST_ADVANTIX_TEST_7,
    CONST_ADVANTIX_TEST_8,
    CONST_ADVANTIX_TEST_9,
    ERR_IMPORT_ERROR_3,
)

from crop.ingress import (
    advantix_read_csv,
    advantix_check_structure,
    advantix_import,
    advantix_convert,
    advantix_df_validity,
)


def test_advantix_read_csv():

    file_path = os.path.join(
        CONST_TEST_DIR_DATA, CONST_ADVANTIX_FOLDER, CONST_ADVANTIX_TEST_1
    )
    data_df = advantix_read_csv(file_path)
    # counting the number of entries
    assert len(data_df.index) == 75


def test_advantix_check_structure():

    file_path = os.path.join(
        CONST_TEST_DIR_DATA, CONST_ADVANTIX_FOLDER, CONST_ADVANTIX_TEST_1
    )
    data_df = advantix_read_csv(file_path)
    success, _ = advantix_check_structure(data_df)
    assert True == success

    file_path = os.path.join(
        CONST_TEST_DIR_DATA, CONST_ADVANTIX_FOLDER, CONST_ADVANTIX_TEST_2
    )
    data_df = advantix_read_csv(file_path)
    success, _ = advantix_check_structure(data_df)
    assert False == success


def test_advantix_convert():

    # Good data
    file_path = os.path.join(
        CONST_TEST_DIR_DATA, CONST_ADVANTIX_FOLDER, CONST_ADVANTIX_TEST_1
    )
    data_df = advantix_read_csv(file_path)
    success, _, data_df = advantix_convert(data_df)
    assert True == success

    # One column is misppeled, the checks should pick this up and return None
    file_path = os.path.join(
        CONST_TEST_DIR_DATA, CONST_ADVANTIX_FOLDER, CONST_ADVANTIX_TEST_2
    )
    data_df = advantix_read_csv(file_path)
    success, _, data_df = advantix_convert(data_df)
    assert False == success
    assert None == data_df

    file_path = os.path.join(
        CONST_TEST_DIR_DATA, CONST_ADVANTIX_FOLDER, CONST_ADVANTIX_TEST_3
    )
    data_df = advantix_read_csv(file_path)
    success, _, data_df = advantix_convert(data_df)
    assert False == success
    assert None == data_df

    file_path = os.path.join(
        CONST_TEST_DIR_DATA, CONST_ADVANTIX_FOLDER, CONST_ADVANTIX_TEST_4
    )
    data_df = advantix_read_csv(file_path)
    success, _, data_df = advantix_convert(data_df)
    assert False == success

    file_path = os.path.join(
        CONST_TEST_DIR_DATA, CONST_ADVANTIX_FOLDER, CONST_ADVANTIX_TEST_5
    )
    data_df = advantix_read_csv(file_path)
    success, _, data_df = advantix_convert(data_df)
    assert False == success

    file_path = os.path.join(
        CONST_TEST_DIR_DATA, CONST_ADVANTIX_FOLDER, CONST_ADVANTIX_TEST_6
    )
    data_df = advantix_read_csv(file_path)
    success, _, data_df = advantix_convert(data_df)
    assert False == success

    file_path = os.path.join(
        CONST_TEST_DIR_DATA, CONST_ADVANTIX_FOLDER, CONST_ADVANTIX_TEST_7
    )
    data_df = advantix_read_csv(file_path)
    success, _, data_df = advantix_convert(data_df)
    assert False == success

    file_path = os.path.join(
        CONST_TEST_DIR_DATA, CONST_ADVANTIX_FOLDER, CONST_ADVANTIX_TEST_8
    )
    data_df = advantix_read_csv(file_path)
    success, log, _ = advantix_convert(data_df)
    assert False == success
    assert ERR_IMPORT_ERROR_3 == log


def test_advantix_import():

    # One column is misppeled, the checks should pick this up and return None
    file_path = os.path.join(
        CONST_TEST_DIR_DATA, CONST_ADVANTIX_FOLDER, CONST_ADVANTIX_TEST_2
    )
    success, _, data_df = advantix_import(file_path)
    assert False == success
    assert None == data_df

    file_path = os.path.join(
        CONST_TEST_DIR_DATA, CONST_ADVANTIX_FOLDER, CONST_ADVANTIX_TEST_1
    )
    success, _, data_df = advantix_import(file_path)

    # counting the number of entries
    assert len(data_df.index) == 75


def test_advantix_df_validity():

    file_path = os.path.join(
        CONST_TEST_DIR_DATA, CONST_ADVANTIX_FOLDER, CONST_ADVANTIX_TEST_9
    )
    data_df = advantix_read_csv(file_path)

    success, _, data_df = advantix_convert(data_df)
    assert success

    success, _ = advantix_df_validity(data_df)
    assert False == success

    file_path = os.path.join(
        CONST_TEST_DIR_DATA, CONST_ADVANTIX_FOLDER, CONST_ADVANTIX_TEST_1
    )
    data_df = advantix_read_csv(file_path)

    success, _, data_df = advantix_convert(data_df)
    assert success

    success, _ = advantix_df_validity(data_df)
    assert True == success
