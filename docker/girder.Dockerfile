#  ========================
#  == CLIENT BUILD STAGE ==
# # ========================
FROM node:16 as client-builder
WORKDIR /app

# Install dependencies
COPY client/package.json client/yarn.lock /app/
RUN yarn install --frozen-lockfile --network-timeout 300000
# Build
COPY .git/ /app/.git/
COPY client/ /app/
RUN yarn build:web

# # ========================
# # == SERVER BUILD STAGE ==
# # ========================
# # Note: server-builder stage will be the same in both dockerfiles
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
# Install dependencies only
RUN poetry install --no-root
# Build girder client, including plugins like worker/jobs
RUN girder build
# Copy full source code and install
COPY server/ /opt/UMD/src/
RUN poetry install --only main
# =================
# == DIST SERVER ==
# =================
FROM python:3.8-slim-buster as server

# Hack: Tell GitPython to be quiet, we aren't using git
ENV GIT_PYTHON_REFRESH="quiet"
ENV PATH="/opt/UMD/local/venv/bin:$PATH"

# Copy site packages and executables
COPY --from=server-builder /opt/UMD/local/venv /opt/UMD/local/venv
# Copy the source code of the editable module
COPY --from=server-builder /opt/UMD/src /opt/UMD/src
COPY --from=server-builder /opt/dive/server /opt/dive/server
# Copy the client code into the static source location
COPY --from=client-builder /app/dist/ /opt/UMD/local/venv/share/girder/static/viame/
# Install startup scripts
COPY docker/entrypoint_server.sh docker/server_setup.py /
ENTRYPOINT [ "/entrypoint_server.sh" ]
