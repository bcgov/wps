# NOTE:
# This Dockerfile is for local development only!

# debian would match more closely what we have in production, and would probably be ideal,
# but it's also a pain working with because debian is so old.
FROM ubuntu:22.04

ARG USERNAME=worker
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Tell r-base not to wait for interactive input.
ENV DEBIAN_FRONTEND=noninteractive

# Install dependancies needed by python developer packages
# One should really run all these installs and the update in one go - for a consistent install
# but ease of development trumps consistency in this instance: it's easer to have more
# faster running steps that can fail, that one big monster install that takes forever 
# and fails.
# NOTE: Once we no longer need pyodbc, please remove the apt-get update and install commands below.
RUN apt-get -y update
RUN apt-get -y install unixodbc-dev
# Install old (2.4.*; current debian) version of gdal
# cffdrs requires libudunits2-dev
RUN apt-get -y install libgdal-dev libudunits2-dev

# Install R
RUN apt-get update --fix-missing && apt-get -y install r-base

# Install cffdrs
RUN R -e "install.packages('cffdrs')"

# Install some other dependancies
RUN apt-get -y install git build-essential python3 python3-dev python3-pip curl vim

# Install JDK
RUN apt-get -y install default-jdk

# We could install poetry manually, but it's easier to use apt.
RUN apt-get -y install python3-poetry
# Poetry expects "python", but by default, on ubuntu, you need to specify "python3", so
# we work around that, by using the python3-poetry command.
RUN apt-get -y install python-is-python3

# from: https://code.visualstudio.com/remote/advancedcontainers/add-nonroot-user
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME

RUN mkdir /app
RUN chown worker /app
USER worker
ENV PATH="/home/worker/.local/bin:${PATH}"

WORKDIR /app

# Update pip
RUN python3 -m pip install --upgrade pip

# Copy poetry files.
COPY pyproject.toml poetry.lock ./

COPY --chown=worker:worker poetry.lock pyproject.toml ./
RUN python3 -m pip install cachecontrol

RUN poetry install

# We can't have this inside pyproject.toml because the gdal version differs from platform to platform.
# To figure out what version of pygdal you need, run gdal-config
RUN poetry run python -m pip install pygdal==3.4.1.10

ENV PATH="/home/worker/.local/bin:${PATH}"

COPY ./app /app/app
# TODO: we need to do this better.
RUN mkdir /app/advisory
COPY ./advisory /app/advisory
RUN mkdir /app/libs
COPY ./libs /app/libs

# root user please
USER 0
# We don't know what user poetry is going to run as, so we give everyone write access directories
# in the app folder. We need write access for .pyc files to be created. .pyc files are good,
# they speed up python.
RUN chmod a+w $(find /app/app -type d)

USER worker

EXPOSE 8080

ENV CLASSPATH=/app/libs/REDapp_Lib.jar:/app/libs/WTime.jar:/app/libs/hss-java.jar:${CLASSPATH}
CMD PYTHONPATH=. poetry run alembic upgrade head && poetry run uvicorn app.main:app --timeout-keep-alive 120 --host 0.0.0.0 --reload --port 8080

