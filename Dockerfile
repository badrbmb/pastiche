FROM python:3.11-slim

ARG DEBIAN_FRONTEND=noninteractive

ENV PYTHONUNBUFFERED 1

RUN apt-get -y update \
  && apt-get -y upgrade \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* \
  && useradd --uid 10001 -ms /bin/bash runner

# create workdir
WORKDIR /home/runner/server

# swap from root to runner user
USER 10001

# make sure usser.s file are on path
ENV PATH="${PATH}:/home/runner/.local/bin"

# install pip and poetry
RUN pip3 install --upgrade pip \
  && pip3 install --no-cache-dir poetry

# Copy rest of files
COPY . .

# install requirements
RUN poetry install --only main

# EXPOSE 8000

CMD poetry run uvicorn pastiche.main:app --host 0.0.0.0 --port $PORT

