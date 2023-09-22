[![Issues](https://img.shields.io/github/issues/bcgov/wps.svg?style=for-the-badge)](/../../issues)
[![MIT License](https://img.shields.io/github/license/bcgov/wps.svg?style=for-the-badge)](/LICENSE)
[![Lifecycle](https://img.shields.io/badge/Lifecycle-Stable-97ca00?style=for-the-badge)](https://github.com/bcgov/repomountie/blob/master/doc/lifecycle-badges.md)
[![codecov](https://codecov.io/gh/bcgov/wps/branch/main/graph/badge.svg?token=QZh80UTLpT)](https://codecov.io/gh/bcgov/wps)

# Wildfire Predictive Services

test

## Description

Wildfire Predictive Services to support decision making in prevention, preparedness, response and recovery.

## Getting Started

### Dependencies

### Installing

#### Running the application locally in docker:

1. Create `.env` file in `web` using `web/.env.example` as a sample.
2. Create `.env.docker` file in `api/app` using `api/app/.env.example` as a sample.
3. Run `docker compose build` and then `docker compose up`
4. Open [http://localhost:8080](http://localhost:8080) to view the front end served up from a static folder by the python api.
5. Open [http://localhost:3000](http://localhost:3000) to view the front end served up in developer mode by node.

#### Developing the application in a dev container, using vscode:

- Open up the project: `Remote-Containers: Open Folder in Container`, select docker-compose.vscode.yml
- Sometimes VSCode doesn't pick up you've changed the docker container: `Remote-Containers: Rebuild Container`
- Install extensions into the container, as needed.
- You can point the API database to: `host.docker.internal`
- You can start up other services outside of vscode, e.g.: `docker compose up db` and `docker compose up redis`

#### Running the api alone

Refer to [api/README.md](api/README.md).

#### Running the front end alone

Refer to [web/README.md](web/README.md)

### Documentation

- [Database](docs/DB.md)
- [Devops](docs/DEVOPS.md)
- [Conventions](docs/CONVENTIONS.md)
- [Wildfire Glossary](https://github.com/bcgov/wps/wiki/Glossary)

## License

[Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0) License - see the [LICENSE.md](https://github.com/bcgov/wps/blob/main/LICENSE)

## Contributing

### PRs

Your Github PR is required to pass all our CI checks, including our test coverage threshold via CodeCov: https://docs.codecov.com/docs/about-code-coverage

### Resources

- [Issues](https://github.com/bcgov/wps/issues)
- [ZenHub Board](https://app.zenhub.com/workspaces/wildfire-predictive-services-5e321393e038fba5bbe203b8/board?repos=235861506,237125626,237125691)
- [PEP8](https://github.com/python/peps/blob/master/pep-0008.txt) and [PEP20](https://github.com/python/peps/blob/master/pep-0020.txt) coding conventions, but with 110 character line breaks
- [Code of Conduct](https://github.com/bcgov/wps/blob/master/CONDUCT.md)

## Acknowledgments

[![SonarCloud](https://sonarcloud.io/images/project_badges/sonarcloud-white.svg)](https://sonarcloud.io/dashboard?id=bcgov_wps)
