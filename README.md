# CROP <img src="media/logo.png" width="180" align="right">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation Status](https://readthedocs.org/projects/crop/badge/?version=latest)](https://crop.readthedocs.io/en/latest/?badge=latest)
[![Build Status](https://travis-ci.com/alan-turing-institute/CROP.svg?branch=master)](https://travis-ci.org/alan-turing-institute/CROP)

<!-- [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3662779.svg)](https://doi.org/10.5281/zenodo.3662779) -->

## Summary

**C**rop is a **R**esearch **O**bservations **P**latform designed and created by [Tomas Lazauskas](https://github.com/tomaslaz) and [Flora Roumpani](https://github.com/entopia) in collaboration with [Dr Ruchi Choudhary's](https://www.turing.ac.uk/people/researchers/ruchi-choudhary) research group and [Growing Underground](http://growing-underground.com/).

The overall aim of the CROP project is to prototype a digital twin of the [Growing Underground](http://growing-underground.com/)'s underground farm which:
* collects heterogeneous IoT sensor data,
* provides 3D visualisation of the underground farm and sensor locations,
* helps to analyse farm conditions at various points in time.

<br/>
<p align="center">
  <img src="media/webapp.png" width="600">
</p>
<br/>

## Disclaimer

CROP is a **development** code and we recommend that you do not deploy this **prototype** application in a production setting. The implementation is only for demonstration purposes only and we make no warranties of any kind, express or implied, about the completeness, accuracy, reliability, suitability or availability with respect to the web app, backend infrastructure or the information.

## Key Functionality

## Implementation

CROP is implemented using a well established software stack (given below) and exploits four different services on the Azure cloud computing platform.

### Solution / Software stack

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


### Development credits

[Gentelella](https://github.com/afourmy/flask-gentelella) - a free to use (MIT license) Bootstrap admin template on which the webapp is built.

## Deployment

#### Continuous Deployment

We employ a continuous delivery toolchain with Docker on Travis CI which publishes Docker images automatically when PR is made to the *master* branch.

#### Manual

Steps of how to set up and deploy CROP locally or on Azure are documented [here](utils/deployment.md).

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
