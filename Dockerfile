FROM turingcropapp/webappbase:latest

# Upgrading python and installing python libraries
COPY requirements.txt /
RUN apt update
RUN apt install -y python3.8 python3.8-dev libpython3.8 python3.8-venv
RUN rm /usr/bin/python3 && ln -s /usr/bin/python3.8 /usr/bin/python3
RUN ls -l /usr/bin | grep python
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r /requirements.txt && rm -rf ~/.cache/pip /requirements.txt

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
