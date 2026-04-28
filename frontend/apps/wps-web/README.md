# Wildfire Predictive Services Web Application

## Description

Wildfire Predictive Services to support decision making in prevention, preparedness, response and recovery.

For setup and development instructions, see the [monorepo README](../../README.md).

## Config

In `openshift/templates/global.config.yaml` there is a template for a global ConfigMap. This template can be applied to the Openshift project from the command line. For example, to apply the global.config template and pass a value for the VITE_KEYCLOAK_REALM parameter, run

`oc -n <openshift-project-name> process -f openshift/templates/global.config.yaml -p VITE_KEYCLOAK_REALM=<realm-name> | oc create -f -`

## License

This project is licensed under the [Apache License, Version 2.0](https://github.com/bcgov/wps/blob/main/LICENSE).

## Contributing

Frontend changes should follow [MaterialUI](https://material.io) design as closely as possible, leveraging the [Material-UI React implementation library](https://mui.com), unless [decided otherwise](https://github.com/bcgov/wps/wiki/Frontend-Design-Decisions).

## Acknowledgments

- [Create React App](https://github.com/facebook/create-react-app/)
- [Redux Toolkit - advanced tutorial](https://redux-toolkit.js.org/tutorials/advanced-tutorial/)

[![SonarCloud](https://sonarcloud.io/images/project_badges/sonarcloud-white.svg)](https://sonarcloud.io/dashboard?id=bcgov_wps)
