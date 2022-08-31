# CROP <img src="media/logo.png" width="180" align="right">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)[![Build Status](https://app.travis-ci.com/alan-turing-institute/CROP.svg?branch=main)](https://app.travis-ci.com/alan-turing-institute/CROP)

**C**ROP is a **R**esearch **O**bservations **P**latform designed and created by the [Research Engineering Group](https://www.turing.ac.uk/research/research-engineering) at the Alan Turing Institute in collaboration with [Dr Ruchi Choudhary's](https://www.turing.ac.uk/people/researchers/ruchi-choudhary) research group and [Growing Underground](http://growing-underground.com/).

## Summary

The aim of CROP is to prototype a digital twin of the [Growing Underground](http://growing-underground.com/) underground farm.

CROP is an on cloud-based application which utilizes the flexibility, customization and evolution that a cloud-native system provides, to better refine, simplify and improve the processes and architecture of the system with regards to our research needs.

The digital twin:
* collects heterogeneous IoT sensor data,
* provides 3D visualisation of the underground farm and sensor locations,
* helps to analyse and forecast farm conditions at various points in time.

<br/>
<p align="center">
  <img src="media/webapp.png" width="600">
</p>

## Key Functionalities

- The CROP web application is the main interface for the digital twin. Users can
    - explore collected heterogeneous IoT sensor data,
    - analyse farm conditions at various points in time,
    - use the interactive 3D visualisation of the farm,
    - forecast future farm conditions using machine learning models built into the platform.
- The CROP database is constantly updated from multiple streams of data: Hyper API, Stark energy usage platform, and others.
- For forecasting, we CROP uses two models
    - An ARIMA model uses past temperature and relative humidity data in the farm to forecast conditions a few days into the future.
    - A GES model uses past sensor data, weather data, farm operational parameters (lighting schedules, fan settings, etc.) and Gaussian processes to forecast conditions a few days into the future. The GES model has the ability to predict various alternative scenarios, such as how would conditions change if the lights were switched on at a different time, or the fan settings were changed.

The Unity 3D model is found in [this repo](http://github.com/alan-turing-institute/CROP_unity)
<br/>
<p align="center">
  <img src="media/infrastructure.png" width="600">
</p>

## Implementation

CROP is implemented using a well established software stack (given below) and exploits four different services on the Azure cloud computing platform.

### Software stack

<table style="text-align:center">
  <thead>
    <tr>
      <th>Platform</th>
      <th>Service</th>
      <th>Software</th>
    </tr>
  </thead>
  <tbody>
    <tr>
        <td rowspan=4><img src="media/stack/azure_logo.png" width=200></td>
        <td>
          <img src="media/stack/azure_function_logo.png" width=100>
          </br>Function
        </td>
        <td rowspan=4 style='width: 200px'>
          <img src="media/stack/python_logo.png" height=50></br>
          <img src="media/stack/flask_logo.png" width=50></br>
          <img src="media/stack/bootstrap_logo.png" width=50></br>
          <img src="media/stack/html5_logo.png" height=50></br>
          <img src="media/stack/jinja_logo.png" height=50></br>
          <img src="media/stack/sqlalchemy_logo.png" height=50></br>
          <img src="media/stack/unity_logo.png" height=50></br>
          <img src="media/stack/docker_logo.png" height=50></br>
        </td>
    </tr>
    <tr>
        <td>
          <img src="media/stack/azure_webapp_logo.png" width=100>
          </br>WebApp
        </td>
    </tr>
    <tr>
        <td>
          <img src="media/stack/azure_storage_logo.png" width=100>
          </br>Storage
        </td>
    </tr>
    <tr>
        <td>
          <img src="media/stack/azure_pg_logo.png" width=200>
          </br>PostgreSQL
        </td>
    </tr>
  </tbody>
</table>

### Repository structure
The directories are structured as follows:
* `core` has all the code for interacting with the database.
This includes defining the database schema in `structure.py`, some utilities, and modules for each of the ingress functions, for reading and writing the data from various sensors and other data sources.
* `tests` has the test suite for `core`.
* `webapp` has the Flask webapp.
* `ingress_functions` has the configurations and code for the Azure functions for importing data into the database.
The code itself for each function is nearly trivial:
It just calls the corresponding function in `core`.
This folder mainly exists to hold the `host.json` and `function.json` files for each function.
* `models` has the code for the forecasting models, ARIMA and GES.
* `media` has illustrations, logos, etc.
* `util_scripts` has various utilities that don't fit the other categories.
* `.secrets` has shell scripts for setting environment variables with secrets, such as database passwords, to facilitate running a local copy of the webapp for development use.
The version-controlled files are merely templates, to be filled in with the actual values for the secrets.

All of `tests`, `webapp`, `ingress_functions`, `util_scripts`, and `models` import and use various parts of `core`. None of them import from or talk to each other.

The repository root also has three Docker files:
* `Dockerfile_ingress_functions` builds a container that holds all the functions in `ingress_functions`, in an environment to run them on an Azure function app.
* `Dockerfile_webapp` builds the webapp, ready to be deployed as an Azure app service. It builds on `webappbase`.
* `Dockerfile_webappbase` is a container that installs some of the dependencies needed by the webapp.
It's separated from `webapp` to improve build times, and shouldn't need to be rebuilt except in rare circumstances.

Note that even though the GES model also runs as an Azure function app, it has no Dockerfile. This is because it is deployed directly from the Github Action.

Some of the subfolders have their own READMEs. See them for more details of each part.

### Development credits

[Gentelella](https://github.com/afourmy/flask-gentelella) - a free to use (MIT license) Bootstrap admin template on which the webapp is built.

## Deployment

We employ a continuous delivery toolchain using Github Actions which deploys the latest version of CROP when a push or a PR is made to the `main` or `develop` branches.
The Github Actions
* Build a Docker container for the webapp, and push it to Docker Hub.
* Build a Docker container for the Azure function apps that collect data into the database (ingress functions), and push it to Docker Hub.
* Publish the Azure function app for running the forecasting models.
* Run the CROP test suite.

The Azure services for the webapp and the ingress functions listen to updates on Docker Hub, and deploy the latest container once it has been pushed to the Hub.

`main` and `develop` are deployed to production and testing versions of the platform, respectively. The former is relatively stable, the latter may be broken in the course of development.

## Getting help

If you found a bug or need support, please submit an issue [here](https://github.com/alan-turing-institute/CROP/issues/new).

## How to contribute

We welcome contributions! If you are willing to propose new features or have bug fixes to contribute, please submit a pull request [here](https://github.com/alan-turing-institute/CROP/pulls).

<hr/>

<p align="center">
  <img src="media/partners/turing.png" width="200">
  &nbsp;&nbsp;&nbsp;
  <img src="media/partners/cambridge.jpg" width="200" width="200">
  &nbsp;&nbsp;&nbsp;
  <img width="200" src="media/partners/growing_underground.png">
</p>
