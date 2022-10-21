# Ingress of data into the CROP database

[Azure functions](https://docs.microsoft.com/en-us/azure/azure-functions/) are used to upload data to the CROP database.
These make use of a Docker container that is build using the [Dockerfile](Dockerfile) in this directory, by a Github Action specified [here](../.github/workflows/functions-docker.yaml) upon pushes or merges to the `main` or `develop` branches.

The functions to be run are specified by directories called `xxx_func` in this directory.  Each of these has an `__init__.py` which defines the main function to be run, and a `function.json` file that includes information about how the function should be triggered.

In order to update the function apps on Azure, the best approach seems to be to tear them down and recreate them, using the script [create_functionapps.sh](../utils/create_azure_infrastructure/scripts/create_functionapps.sh).   See also the instructions [here](../utils/create_azure_infrastructure/README.md).

## Currently used functions

### hyper_func

Fetches data from the [hyper.ag](https://hyper.ag/) API, and fills the table "aranet_trh_data".  Runs once per hour.

### weather_func

Fetches historical weather data from [openweathermap](https://openweathermap.org/) API and fills the table "iweather".  Runs every 12 hours.

### weather_forecast_func

Fetches forecast weather data from [openweathermap](https://openweathermap.org/) API and fills the table "weather_forecast".  Runs every 12 hours.

### electricity_func

Gets data from Stark, and fills the table "utc_energy_data".  Runs once per day.
