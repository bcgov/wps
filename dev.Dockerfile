FROM python:3.8-buster

# spotwx has an old certificate, so we have to make debian more forgiving.
RUN sed -i 's/TLSv1.2/TLSv1.0/g' /etc/ssl/openssl.cnf

WORKDIR /app
COPY . .

RUN python -m pip install --upgrade pip

# Install pipenv.
RUN python -m pip install pipenv

# Install dependancies need by python developer packages
# NOTE: Once we no longer need pyodbc, please remove the apt-get update and install commands below.
RUN apt-get -y update
RUN apt-get -y install unixodbc-dev

RUN python -m pipenv install --dev

EXPOSE 8080

CMD pipenv run uvicorn main:APP --reload --host 0.0.0.0 --port 8080