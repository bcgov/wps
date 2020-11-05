# Wildfire Predictive Services Web Application

## Description

Wildfire Predictive Services to support decision making in prevention, preparedness, response and recovery.

## Getting Started

### Dependencies

- [Node.js](https://nodejs.org/en/) - You’ll need to have Node >= 10.x and npm >= 5.6 on your machine. You can use [nvm](https://github.com/nvm-sh/nvm#installation) (macOS/Linux) or [nvm-windows](https://github.com/coreybutler/nvm-windows#node-version-manager-nvm-for-windows) to switch Node versions between different projects.

Note: We are using Node 10 as a base image on our pipeline.

### Installing

In the project directory, run:

#### `npm install`

Installs all dependencies in the node_modules folder.

### Executing program

In the project directory, create `.env` file at root using `.env.example` as a sample, then you can run:

#### `npm start`

Runs the app in the development mode.
The page will reload if you make edits. You will also see any lint errors in the console.

#### `npm test`

Launches the test runner in the interactive watch mode.

#### `npm run build`

Builds the app for production to the `build` folder.
It correctly bundles React in production mode and optimizes the build for the best performance.

##### Running the application in docker:

1. Create `.env` file at root using `.env.example` as a sample
2. Run `docker-compose build` and then `docker-compose up`
3. Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

## Config

In `openshift/templates/global.config.yaml` there is a template for a global ConfigMap. This template can be applied to the Openshift project from the command line. For example, to apply the global.config template and pass a value for the REACT_APP_KEYCLOAK_REALM parameter, run

`oc -n <openshift-project-name> process -f openshift/templates/global.config.yaml -p REACT_APP_KEYCLOAK_REALM=<realm-name> | oc create -f -`

## Contributing

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

## License

This project is licensed under the [Apache License, Version 2.0](https://github.com/bcgov/wps-web/blob/main/LICENSE).

## Acknowledgments

Inspiration, code snippets, etc.

- [Create React App](https://github.com/facebook/create-react-app/)
- [Redux Toolkit - advanced tutorial](https://redux-toolkit.js.org/tutorials/advanced-tutorial/)

[![SonarCloud](https://sonarcloud.io/images/project_badges/sonarcloud-white.svg)](https://sonarcloud.io/dashboard?id=bcgov_wps-web)

Template copied from

- [DomPizzie](https://gist.github.com/DomPizzie/7a5ff55ffa9081f2de27c315f5018afc)
