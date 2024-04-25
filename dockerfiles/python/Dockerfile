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

RUN mkdir -p /opt/python/scraping_tp
WORKDIR /opt/python/scraping_tp

RUN groupadd -g ${GID} ${USERNAME} \
  && useradd -u ${UID} -g ${GID} -s /bin/bash -m ${USERNAME}
# RUN useradd --uid ${UID} --create-home --shell /bin/sh -G sudo,root ${USERNAME}
# RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

USER ${UID}

RUN curl -sSL https://install.python-poetry.org | python3 -
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH $PATH:/home/${USERNAME}/.local/bin::/home/${USERNAME}/.cargo/bin
RUN poetry config virtualenvs.in-project true
RUN cargo install geckodriver

RUN echo 'alias ll="ls -la"' >> ~/.bashrc
