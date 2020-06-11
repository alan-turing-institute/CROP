#!/bin/bash

secrets_file='.secrets/crop.sh'

echo -e '#!/bin/bash\n' > $secrets_file
echo -e 'export CROP_STARK_USERNAME="'$CROP_STARK_USERNAME'"' >> $secrets_file
echo -e 'export CROP_STARK_PASS="'$CROP_STARK_PASS'"' >> $secrets_file

echo -e 'export CROP_SQL_USER="'$CROP_SQL_USER'"' >> $secrets_file
echo -e 'export CROP_SQL_PASS="'$CROP_SQL_PASS'"' >> $secrets_file
echo -e 'export CROP_SQL_HOST="'$CROP_SQL_HOST'"' >> $secrets_file
echo -e 'export CROP_SQL_PORT="'$CROP_SQL_PORT'"' >> $secrets_file
echo -e 'export CROP_SQL_DBNAME="'$CROP_SQL_DBNAME'"' >> $secrets_file