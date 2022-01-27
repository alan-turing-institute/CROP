# FROM ubuntu
FROM rocker/r-ver:4.0.5
WORKDIR /models

RUN apt-get -y update
RUN apt -y install curl
RUN apt -y install git-all
RUN apt-get -y subversion
RUN svn checkout https://github.com/alan-turing-institute/CROP/branches/output-to-database/versioning/Data_model/models/static


RUN /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
RUN echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"' >> /root/.profile
RUN eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
RUN brew install gcc
RUN brew install libpq

# If you need to have libpq first in your PATH, run:
RUN echo 'export PATH="/home/linuxbrew/.linuxbrew/opt/libpq/bin:$PATH"' >> ~/.profile

# For compilers to find libpq you may need to set:
RUN export LDFLAGS="-L/home/linuxbrew/.linuxbrew/opt/libpq/lib"
RUN export CPPFLAGS="-I/home/linuxbrew/.linuxbrew/opt/libpq/include"
RUN apt-get -y install libpq-dev

# CMD =[Rscript /code/requirements.R]
RUN Rscript /code/requirements.R
RUN Rscript /code/test_connection.R
