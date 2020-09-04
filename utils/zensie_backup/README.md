# Zensie Backup

Script to backup 30 MHz sensor data using Zensie API.

The routine uses api key to connect to the ZENSIE API and iterates through a list of sensors (**config.yml**). Backed up data is saved into a new folder as separate compressed (zip) csv files for each sensor.

### Usage

    usage: zensie_backup.py [-h] [--dfrom DFROM] [--dto DTO] [--fconfig FCONFIG]

    Backs up 30MHz Sensor Data using Zensie API.

    optional arguments:
      -h, --help         show this help message and exit
      --dfrom DFROM      Backup period start date, e.g. 2020-08-01 (default: today
                         - 30 days).
      --dto DTO          Backup period end date, e.g. 2020-08-20 (default: today).
      --fconfig FCONFIG  YAML config file (default: config.yml).

### Example:

    python zensie_backup.py --dfrom '2020-08-01' --dto '2020-08-10'
