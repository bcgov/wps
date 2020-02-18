FROM python:3.6
WORKDIR /usr/src/app
RUN pip install pipenv
COPY Pipfile* /tmp/
RUN cd /tmp && pipenv lock --requirements > requirements.txt
RUN pip install -r /tmp/requirements.txt
COPY . .
EXPOSE 8080
CMD uvicorn main:app --reload --host 0.0.0.0 --port 8080