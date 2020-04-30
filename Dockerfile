# Multistage dockerfile

####
# Stage 0:
#
# We need a requirements.txt, but we don't need pipenv installed in our final image,
# so we do a multistage build where we generate the requirements.txt in our first stage,
# and consume it in our final stage.
# TODO: This slows down the build somewhat, look at alternatives.
FROM python:3.6
# Install pipenv.
RUN python -m pip install pipenv
# Copy Pipfile and Pipfile.lock.
COPY Pipfile* /tmp/
# Generate a requirements.txt file, which contains a list of all our project dependancies.
RUN cd /tmp && pipenv lock --requirements > requirements.txt

####
# Stage 1:
#
# We now start a nice clean build - that has only the bare minimum of what we need

FROM python:3.6

# Copy the requirements.txt from the 1st stage of the build.
COPY --from=0 /tmp/requirements.txt /tmp
# Install all our package requirements.
RUN python -m pip install -r /tmp/requirements.txt

WORKDIR /app
COPY . .

EXPOSE 8080

CMD gunicorn main:APP -w 4 -k uvicorn.workers.UvicornWorker -b :8080