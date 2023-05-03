FROM python:3.9-slim
WORKDIR /testing
COPY . /testing

ENV MAKEFLAGS="-j10"

RUN apt-get update && apt-get install -y libpq-dev gcc ssh git
RUN \
    pip install --upgrade pip && \
    pip install --upgrade setuptools && \
    pip install python-dotenv && \
    pip install -r requirements_dev.txt && \
    mkdir /root/.ssh/

ADD docker_runner /root/.ssh/id_rsa
RUN \
    touch /root/.ssh/known_hosts && \
    ssh-keyscan tessgit.mit.edu >> /root/.ssh/known_hosts && \
    git clone git@tessgit.mit.edu:wcfong/configurables.git && \
    cd configurables && pip install . && cd .. \
