FROM python:3.9.18-slim

ARG UID
ARG GID
ARG USERNAME

RUN apt-get update -y && \
    apt-get upgrade -y && \
    apt-get install -y \
    sudo \
    git \
    curl \
    vim \
    python3-dev \
    default-mysql-client \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    gettext \
    chromium-driver \
    firefox-esr \
    xvfb

 RUN curl -fL -o /tmp/geckodriver.tar.gz \
     https://github.com/mozilla/geckodriver/releases/download/v0.34.0/geckodriver-v0.34.0-linux-aarch64.tar.gz && \
     tar -xzf /tmp/geckodriver.tar.gz -C /tmp/ && \
     chmod +x /tmp/geckodriver && \
     mv /tmp/geckodriver /usr/local/bin/

RUN mkdir -p /opt/python/scraping_tp
WORKDIR /opt/python/scraping_tp

RUN groupadd -g ${GID} ${USERNAME} \
  && useradd -u ${UID} -g ${GID} -s /bin/bash -m ${USERNAME}
# RUN useradd --uid ${UID} --create-home --shell /bin/sh -G sudo,root ${USERNAME}
# RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

USER ${UID}

RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH $PATH:/home/${USERNAME}/.local/bin
RUN poetry config virtualenvs.in-project true

RUN echo 'alias ll="ls -la"' >> ~/.bashrc
