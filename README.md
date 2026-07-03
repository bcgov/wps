[![Issues](https://img.shields.io/github/issues/bcgov/wps.svg?style=for-the-badge)](/../../issues)
[![MIT License](https://img.shields.io/github/license/bcgov/wps.svg?style=for-the-badge)](/LICENSE)
[![Lifecycle](https://img.shields.io/badge/Lifecycle-Stable-97ca00?style=for-the-badge)](https://github.com/bcgov/repomountie/blob/master/doc/lifecycle-badges.md)
[![codecov](https://codecov.io/gh/bcgov/wps/branch/main/graph/badge.svg?token=QZh80UTLpT)](https://codecov.io/gh/bcgov/wps)

# Wildfire Predictive Services

## Description

Wildfire Predictive Services to support decision making in prevention, preparedness, response and recovery.

## Getting Started

### Dependencies

> **Note:** Docker Compose and the VS Code dev container are **currently
> unsupported**. Native setup is the recommended (and supported) way to run the
> project locally.

Run the backend and front end natively — see the per-component setup docs:

- Backend: [backend/README.md](backend/README.md) (uv, GDAL, Postgres/PostGIS, Redis). On macOS, `setup/mac.sh` installs the system dependencies.
- Frontend: [web/README.md](web/README.md) (Node/yarn).

### Installing

Native setup is the recommended and supported path. The Docker Compose and dev
container flows further down are **currently unsupported** and may be out of date.

#### Running the api (native — recommended)

Refer to [backend/packages/wps-api/README.md](backend/packages/wps-api/README.md) (setup in [backend/README.md](backend/README.md); on macOS, `setup/mac.sh` installs the dependencies).

#### Running the front end (native — recommended)

Refer to [web/README.md](web/README.md)

#### Running the application locally in docker (currently unsupported)

1. Create `web/.env` using `web/apps/wps-web/.env.example` as a sample.
2. Create `backend/packages/wps-api/src/app/.env.docker` using the repo-root `.env.example` as a sample.
3. Run `docker compose build` and then `docker compose up`
4. Open [http://localhost:8080](http://localhost:8080) to view the front end served up from a static folder by the python api.
5. Open [http://localhost:3000](http://localhost:3000) to view the front end served up in developer mode by node.

#### Developing the application in a dev container, using vscode (currently unsupported)

- Open the project and run `Dev Containers: Reopen in Container` — VS Code picks up `.devcontainer/devcontainer.json`.
- Sometimes VSCode doesn't pick up you've changed the docker container: `Dev Containers: Rebuild Container`
- Install extensions into the container, as needed.
- You can point the API database to: `host.docker.internal`
- You can start up other services outside of vscode, e.g.: `docker compose up db` and `docker compose up redis`

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
- [PEP8](https://github.com/python/peps/blob/master/pep-0008.txt) and [PEP20](https://github.com/python/peps/blob/master/pep-0020.txt) coding conventions, but with 110 character line breaks
- [Code of Conduct](https://github.com/bcgov/wps/blob/master/CONDUCT.md)

## Acknowledgments

[![SonarCloud](https://sonarcloud.io/images/project_badges/sonarcloud-white.svg)](https://sonarcloud.io/dashboard?id=bcgov_wps)
