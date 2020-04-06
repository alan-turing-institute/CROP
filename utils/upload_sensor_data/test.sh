#!/bin/bash

python upload_sensor_data.py \
  --storageacc $CROP_TEST_STORAGE_ACC \
  --container $CROP_TEST_CONT_ADVANTICSYS \
  --connectionstr $CROP_TEST_STORAGE_CONN_STR \
  --source ../../core/tests/data/Advanticsys/data-20190821-test1.csv \
  --target 20190821-test1.csv
