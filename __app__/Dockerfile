# To enable ssh & remote debugging on app service change the base image to the one below
# FROM mcr.microsoft.com/azure-functions/python:2.0-python3.7-appservice
FROM mcr.microsoft.com/azure-functions/python:3.0-python3.8


ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true

# 0. Install essential packages
RUN apt-get update \
    && apt-get install -y \
        build-essential \
        cmake \
        git \
        wget \
        unzip \
    && rm -rf /var/lib/apt/lists/*

# . Install requirements
RUN pip install --upgrade pip
COPY requirements.txt /
RUN pip install -r /requirements.txt

# . Copy python code to image
COPY . /home/site/wwwroot
