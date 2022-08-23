#!/bin/bash

python upload_sensor_data.py \
  --container $CROP_TEST_CONT_ADVANTICSYS \
  --connectionstr $CROP_TEST_STORAGE_CONN_STR \
  --source ../../tests/data/Advanticsys/data-20190821-test1.csv \
  --target 20190821-test1.csv
