# ========================
# == SERVER BUILD STAGE ==
# ========================
# Note: server-builder stage will be the same in both dockerfiles
FROM python:3.8-buster as server-builder

WORKDIR /opt/UMD/src

# https://cryptography.io/en/latest/installation/#debian-ubuntu
RUN apt-get update
RUN apt-get install -y build-essential libssl-dev libffi-dev python3-dev cargo npm python3-distutils
# Recommended poetry install https://python-poetry.org/docs/master/#installation
RUN curl -sSL https://install.python-poetry.org | POETRY_VERSION=1.2.0 POETRY_HOME=/opt/UMD/poetry python -
ENV PATH="/opt/UMD/poetry/bin:$PATH"
# Create a virtual environment for the installation
RUN python -m venv /opt/UMD/local/venv
# Poetry needs this set to recognize it as ane existing environment
ENV VIRTUAL_ENV="/opt/UMD/local/venv"
ENV PATH="/opt/UMD/local/venv/bin:$PATH"

RUN cd /opt && \
    git clone https://github.com/Kitware/dive && \
    cd /opt/dive/server

WORKDIR /opt/dive/server
# Remove the unwanted plugins from the pyproject.toml file
RUN sed -i '/bucket_notifications/d' ./pyproject.toml
RUN sed -i '/rabbitmq_user_queues/d' ./pyproject.toml

RUN poetry env use system
RUN poetry config virtualenvs.create false
RUN poetry install --no-root
RUN poetry install


WORKDIR /opt/UMD/src
COPY server/pyproject.toml server/poetry.lock /opt/UMD/src/
# Copy only the lock and project files to optimize cache
# Use the system installation
RUN poetry env use system
RUN poetry config virtualenvs.create false

# Install dependencies only
RUN poetry install --no-root
# Build girder client, including plugins like worker/jobs
RUN girder build
# Copy full source code and install
COPY server/ /opt/UMD/src/
RUN poetry install --only main

# ====================
# == FFMPEG FETCHER ==
# ====================
FROM python:3.8-buster as ffmpeg-builder
RUN wget -O ffmpeg.tar.xz https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
RUN mkdir /tmp/ffextracted
RUN tar -xvf ffmpeg.tar.xz -C /tmp/ffextracted --strip-components 1

# =================
# == DIST WORKER ==
# =================
FROM python:3.8-buster as worker
# VIAME install at /opt/noaa/viame/
# VIAME pipelines at /opt/noaa/viame/configs/pipelines/

# install tini init system
ENV TINI_VERSION v0.19.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
RUN chmod +x /tini

# Create user "dive" 1099:1099 to align with base image permissions.
# https://github.com/VIAME/VIAME/blob/master/cmake/build_server_docker.sh#L123
RUN useradd --create-home --uid 1099 --shell=/bin/bash umd
# Create a directory for VIAME Addons which won't be used
RUN install -g umd -o umd -d /tmp/addons

# Switch to the new user
USER umd

# Setup the path of the incoming python installation
ENV PATH="/opt/UMD/local/venv/bin:$PATH"

# Copy the built python installation
COPY --chown=umd:umd --from=server-builder /opt/UMD/local/venv/ /opt/UMD/local/venv/
# Copy the source code of the editable module
COPY --chown=umd:umd --from=server-builder /opt/UMD/src /opt/UMD/src
COPY --chown=umd:umd --from=server-builder /opt/dive/server /opt/dive/server

# Copy ffmpeg
COPY --from=ffmpeg-builder /tmp/ffextracted/ffmpeg /tmp/ffextracted/ffprobe /opt/UMD/local/venv/bin/
# Copy provision scripts
COPY --chown=umd:umd docker/entrypoint_worker.sh /

ENTRYPOINT ["/tini", "--"]
CMD ["/entrypoint_worker.sh"]
