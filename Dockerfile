FROM turingcropapp/webappbase:latest

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