FROM ubuntu:18.04

RUN apt-get update

RUN apt-get install -y build-essential

RUN apt-get install -y python

RUN apt-get install -y software-properties-common

RUN apt-get update \
  && apt-get install -y python3-pip python3-dev \
  && cd /usr/local/bin \
  && ln -s /usr/bin/python3 python \
  && pip3 install --upgrade pip

# Installing python libraries
COPY requirements.txt /
RUN pip install -r /requirements.txt && rm -rf ~/.cache/pip /requirements.txt

RUN mkdir CROP
WORKDIR CROP

# Adding crop core
ADD __app__ __app__

# Adding crop webapp
ADD webapp webapp

# Adding secrets
ADD .secrets .secrets

# launch the webapp
WORKDIR /CROP/webapp

EXPOSE 5000

CMD ["./run.sh"]