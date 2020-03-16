#!/bin/bash

python upload_sensor_data.py \
  --storageacc $CROP_STORAGE_ACCOUNT \
  --container $CROP_TEST_CONT_ADVANTIX \
  --connectionstr $CROP_TEST_STORAGE_CONN_STR \
  --source ../../core/tests/data/Advantix/data-20190821-test1.csv \
  --target 20190821-test1.csv
