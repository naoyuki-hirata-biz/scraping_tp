FROM python:3.9.18-slim

ARG UID
ARG GID
ARG USERNAME

RUN groupadd -g ${GID} ${USERNAME} \
  && useradd -u ${UID} -g ${GID} -s /bin/bash -m ${USERNAME}

RUN apt-get update -y && \
    apt-get upgrade -y && \
    apt-get install -y \
    git \
    curl \
    vim \
    python3-dev \
    default-mysql-client \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    gettext \
    chromium-driver

RUN mkdir -p /opt/python
WORKDIR /opt/python

USER ${UID}

RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH $PATH:/home/${USERNAME}/.local/bin
RUN poetry config virtualenvs.in-project true

RUN echo 'alias ll="ls -la"' >> ~/.bashrc

