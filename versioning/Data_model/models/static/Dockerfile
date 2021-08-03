# FROM ubuntu
FROM r-base AS base

RUN apt-get -y update
RUN apt install curl

RUN /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
RUN brew install libpq

WORKDIR /models


# RUN Rscript /code/requirements.R
