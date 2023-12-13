FROM python:3.10
LABEL maintainer="contact@illuin.tech"

RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | \
    tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | \
    apt-key --keyring /usr/share/keyrings/cloud.google.gpg  add - && \
    apt-get update -y && apt-get upgrade -y && \
    apt-get install -y gnupg2 curl unzip libportaudio2 git ffmpeg google-cloud-sdk

WORKDIR /server_app/

RUN ln -snf /usr/share/zoneinfo/Europe/Paris /etc/localtime && echo Europe/Paris > /etc/timezone
RUN mkdir -p /server_app/secrets

RUN python -m pip install --upgrade pip

COPY pyproject.toml lockfiles/server.lock ./
RUN pdm install --no-self -L server.lock

COPY ./quiz_generation /server_app/quiz_generation
COPY ./docker-entrypoint.sh /server_app/docker-entrypoint.sh

CMD ["/bin/bash", "/server_app/docker-entrypoint.sh"]
