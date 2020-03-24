# This dockerfile gives you a container with pylint, a development package installed.
# We use the api image, which should already have been created if you're using docker-compose.
FROM wps-api_api:latest
# NOTE: We could have run `pipenv install --dev --system`, but there are some dependancies,
# like pyodbc for accessing MS Access files which complicate things.
# We need pylint to do our linting.
RUN python -m pip install pylint
# Run linting and unit tests
CMD bash -c "./scripts/lint.sh && ./scripts/test.sh"