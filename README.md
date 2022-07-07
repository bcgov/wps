[![Issues](https://img.shields.io/github/issues/bcgov/wps.svg?style=for-the-badge)](/../../issues)
[![MIT License](https://img.shields.io/github/license/bcgov/wps.svg?style=for-the-badge)](/LICENSE)
[![Lifecycle](https://img.shields.io/badge/Lifecycle-Stable-97ca00?style=for-the-badge)](https://github.com/bcgov/repomountie/blob/master/doc/lifecycle-badges.md)
[![codecov](https://codecov.io/gh/bcgov/wps/branch/main/graph/badge.svg?token=QZh80UTLpT)](https://codecov.io/gh/bcgov/wps)

# Wildfire Predictive Services

## Description

Wildfire Predictive Services to support decision making in prevention, preparedness, response and recovery.

## Getting Started

### Dependencies

### Installing

#### Running the application locally in docker:

1. Create `.env` file in `web` using `web/.env.example` as a sample.
2. Create `.env.docker` file in `api/app` using `api/app/.env.example` as a sample.
3. Run `docker-compose build` and then `docker-compose up`
4. Open [http://localhost:8080](http://localhost:8080) to view the front end served up from a static folder by the python api.
5. Open [http://localhost:3000](http://localhost:3000) to view the front end served up in developer mode by node.

#### Running the api alone

Refer to [api/README.md](api/README.md).

#### Running the front end alone

Refer to [web/README.md](api/README.md)

## License

[Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0) License - see the [LICENSE.md](https://github.com/bcgov/wps/blob/main/LICENSE)

## Glossary

A glossary of terms relating to Wildfire that are relevant to Predictive Services can be found at the [Predictive Wildfire Wiki Glossary Page](https://github.com/bcgov/wps/wiki/Glossary)

## Architecture

```mermaid
graph LR

    datamart["Environment Canada MSC Datamart"]

    wf1["WFWX Fire Weather API</br>[Software System]"]

    sso["Red Hat SSO / Keycloak</br>[Idendity Provider]</br>https://oidc.gov.bc.ca"]

    subgraph Wildfire Predictive Services Unit Web Application
        FrontEnd["PSU Single Page Application</br>[Container: Javascript, React]"]

        subgraph PSU API's
            API["API</br>[Container: Python, FastAPI]"]
            CFFDRS_API["CFFDRS API</br>[Container: Python, FastAPI, R]"]
        end

        pg_tileserv["pg_tileserv</br>[Software System]"]
        redis["REDIS</br>[Software System]"]

        subgraph Openshift Cronjobs
            c-haines["C-Haines</br>[Container: Python]</br>Periodically fetch weather data, process and store relevant subset."]
            env-canada["Env. Canada Weather</br>[Container: Python]</br> Periodically fetch weather data, process and store relevant subset."]
            backup["Backup process</br>[Container: Python]"]
        end

        Database[("Database</br>[Container: PostgreSQL, Patroni]</br></br>Weather model data, audit logs,</br>HFI calculator data")]
        Files[("Files</br>[Container: json files, shp files, html files]</br></br>Percentile data, diurnal data, jinja templates")]

    end

    subgraph "S3 Compliant, OCIO Object Storage Service"
        s3[("Object Storage</br>[Container: S3 Compliant]")]
    end

    API-. "Read</br>[S3/HTTPS]" .->s3
    API-.->|"Read</br>[psycopg]"|Database
    API-.->|"Read</br>[JSON/HTTPS]"|CFFDRS_API
    API-.->|"Uses</br>[Reads from disk]"|Files
    API-. "Fetch fire weather data</br>[JSON/HTTPS]" .->wf1
    API-. "Cache WFWX responses" .->redis
    pg_tileserv-. "Read geometries" .->Database
    FrontEnd-.->|"Uses</br>[JSON/HTTPS]"|API
    FrontEnd-.->|"Uses</br>[HTTPS]"|pg_tileserv
    FrontEnd-. "Authenticate</br>[HTTPS]" .->sso
    FrontEnd-. "Read</br>[HTTPS]" .->s3
    c-haines-. "[S3/HTTPS]" .->s3
    c-haines-. "Cache Env. Canada GRIB files" .->redis
    c-haines-. "Download files</br>[GRIB2/HTTPS]" .->datamart
    env-canada-. "Store weather data</br>[psycopg]" .->Database
    env-canada-. "Cache Env. Canada GRIB files" .->redis
    env-canada-. "Download files</br>[GRIB2/HTTPS]" .->datamart
    backup-. "Read</br>[psycopg]" .->Database
    backup-. "[S3/HTTPS] " .->s3

```

### Imagestream flow

![Imagestream flow](./architecture/imagestream_flow.png)

## Contributing

### PRs

Your Github PR is required to pass all our CI checks, including our test coverage threshold via CodeCov: https://docs.codecov.com/docs/about-code-coverage

### Branch naming conventions

Branches must be named in accordance with the rules specified in [.githooks/pre-push](.githooks/pre-push).

- branch names should be informative, meaningful and concise.
- branch names should follow the pattern (category)/(description)/(ticket number)

```
# Enforce branch naming conventions for this project using git hooks.
git config core.hooksPath .githooks
```

example of a good branch name:

```
# Task related to re-factoring of logging, the ticket number being 123:
task/re-factor-logging/123
```

example of a bad branch name:

```
wps-123
```

### How to contribute

Resources:

- [Issues](https://github.com/bcgov/wps/issues)
- [ZenHub Board](https://app.zenhub.com/workspaces/wildfire-predictive-services-5e321393e038fba5bbe203b8/board?repos=235861506,237125626,237125691)
- [PEP8](https://github.com/python/peps/blob/master/pep-0008.txt) and [PEP20](https://github.com/python/peps/blob/master/pep-0020.txt) coding conventions, but with 110 character line breaks
- [Code of Conduct](https://github.com/bcgov/wps/blob/master/CONDUCT.md)

## Acknowledgments

[![SonarCloud](https://sonarcloud.io/images/project_badges/sonarcloud-white.svg)](https://sonarcloud.io/dashboard?id=bcgov_wps)
