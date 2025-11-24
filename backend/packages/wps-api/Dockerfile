# NOTE:
# This Dockerfile is for local development only!

FROM ubuntu:22.04

ARG USERNAME=worker
ARG USER_UID=1000
ARG USER_GID=$USER_UID

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get -y update
RUN apt-get -y install unixodbc-dev libgdal-dev libudunits2-dev

# Install R
RUN apt-get update --fix-missing && apt-get -y install r-base

# Install cffdrs
RUN R -e "install.packages('cffdrs')"

# Install other dependencies
RUN apt-get -y install git build-essential python3 python3-dev python3-pip curl vim

# Install JDK
RUN apt-get -y install default-jdk python-is-python3

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.9.11 /uv /uvx /bin/

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME

RUN mkdir /app && chown worker /app
USER worker
ENV PATH="/home/worker/.local/bin:${PATH}"
WORKDIR /app

# Copy workspace configuration (build context is backend dir)
COPY pyproject.toml /app/
COPY uv.lock /app/
COPY packages/wps-api/pyproject.toml /app/packages/wps-api/
COPY packages/wps-api/README.md /app/packages/wps-api/
COPY packages/wps-shared/pyproject.toml /app/packages/wps-shared/
COPY packages/wps-shared/README.md /app/packages/wps-shared/
COPY packages/wps-shared/src /app/packages/wps-shared/src
RUN chmod -R a-w /app/pyproject.toml /app/uv.lock /app/packages/wps-api /app/packages/wps-shared

# Install dependencies
RUN uv sync --package wps-api
RUN uv pip install pygdal==3.4.1.10

ENV PATH="/app/.venv/bin:${PATH}"
ENV VIRTUAL_ENV="/app/.venv"

COPY packages/wps-api/src/app /app/app
RUN mkdir /app/advisory
COPY packages/wps-api/advisory /app/advisory
RUN mkdir /app/libs
COPY packages/wps-api/libs /app/libs
RUN chmod -R a-w /app/advisory /app/libs

USER 0
RUN chmod a+w $(find /app/app -type d)
USER worker

EXPOSE 8080
ENV CLASSPATH=/app/libs/REDapp_Lib.jar:/app/libs/WTime.jar:/app/libs/hss-java.jar:${CLASSPATH}
CMD PYTHONPATH=. alembic upgrade head && uvicorn app.main:app --timeout-keep-alive 120 --host 0.0.0.0 --reload --port 8080
