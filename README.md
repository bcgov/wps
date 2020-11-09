# Wildfire Predictive Services

## Description

Wildfire Predictive Services to support decision making in prevention, preparedness, response and recovery.

## Getting Started

### Dependencies

#### Fider

Detailed installation instructions for Openshift available on: <https://github.com/garywong-bc/nrm-feedback>

### Installing0

#### Running the application locally in docker:

1. Create `.env` file in `web` using `web/.env.example` as a sample.
2. Create `.env` file in `api/app` using `api/app/.env.example` as a sample.
3. Run `docker-compose -f docker-compose.dev.yml build` and then `docker-compose -f docker-compose.dev.yml up`
4. Open [http://localhost:8080](http://localhost:8080) to view the front end served up from a static folder by the python api.
5. Open [http://localhost:3000](http://localhost:3000) to view the front end served up in developer mode by node.

## License

[Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0) License - see the [LICENSE.md](https://github.com/bcgov/wps/blob/main/LICENSE)

## Glossary

A glossary of terms relating to Wildfire that are relevant to Predictive Services can be found at the [Predictive Wildfire Wiki Glossary Page](https://github.com/bcgov/wps/wiki/Glossary)

## Contributing

### How to contribute

Resources:

- [Issues](https://github.com/bcgov/wps/issues)
- [ZenHub Board](https://app.zenhub.com/workspaces/wildfire-predictive-services-5e321393e038fba5bbe203b8/board?repos=235861506,237125626,237125691)
- [PEP8](https://github.com/python/peps/blob/master/pep-0008.txt) and [PEP20](https://github.com/python/peps/blob/master/pep-0020.txt) coding conventions, but with 110 character line breaks
- [Code of Conduct](https://github.com/bcgov/wps/blob/master/CONDUCT.md)

## Acknowledgments

[![SonarCloud](https://sonarcloud.io/images/project_badges/sonarcloud-white.svg)](https://sonarcloud.io/dashboard?id=bcgov_wps-api)
