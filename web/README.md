# Wildfire Predictive Services Web Application

## Description

Wildfire Predictive Services to support decision making in prevention, preparedness, response and recovery.

## Getting Started

### Dependencies

#### [Node.js](https://nodejs.org/en/)

- You’ll need to have Node >= 10.x and yarn on your machine. You can use [nvm](https://github.com/nvm-sh/nvm#installation) (macOS/Linux) or [nvm-windows](https://github.com/coreybutler/nvm-windows#node-version-manager-nvm-for-windows) to switch Node versions between different projects.
- Note: We are using Node 19 as a base image on our pipeline.
- On ubuntu: `sudo apt install nodejs`

#### [yarn](https://yarnpkg.com/)

- `npm install -g yarn`

### Installing

In the project directory, run:

#### `yarn`

Installs all dependencies in the node_modules folder.

#### Cypress on WSL2

It's possible to configure cypress to run with an X-server with WSL2 and Windows [see this blog entry](https://nickymeuleman.netlify.app/blog/gui-on-wsl2-cypress)

The short version is:

- Launch VcXsrv (remember to check "Disable access control")
- `yarn run cypress`

### Executing program

In the project directory, create `.env` file at root using `.env.example` as a sample, then you can run:

#### `yarn start`

Runs the app in the development mode.
The page will reload if you make edits. You will also see any lint errors in the console.

#### `yarn test`

Launches the jest test runner in the interactive watch mode.
Includes logic only unit tests and [react-testing-library](https://testing-library.com/docs/react-testing-library/intro/) component tests.

#### `yarn cypress`

Launches the cypress test runner in the interactive watch mode.
Includes end-to-end / integration tests for frontend common path interactions.

#### `yarn run build`

Builds the app for production to the `build` folder.
It correctly bundles React in production mode and optimizes the build for the best performance.

##### Running the application in docker:

1. Create `.env` file at root using `.env.example` as a sample
2. Run `docker compose build` and then `docker compose up`
3. Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

## Config

In `openshift/templates/global.config.yaml` there is a template for a global ConfigMap. This template can be applied to the Openshift project from the command line. For example, to apply the global.config template and pass a value for the REACT_APP_KEYCLOAK_REALM parameter, run

`oc -n <openshift-project-name> process -f openshift/templates/global.config.yaml -p REACT_APP_KEYCLOAK_REALM=<realm-name> | oc create -f -`

## License

This project is licensed under the [Apache License, Version 2.0](https://github.com/bcgov/wps/blob/main/LICENSE).

## Contributing

Frontend changes should follow [MaterialUI](https://material.io) design as closely as possible, leveraging the [Material-UI React implementation library](https://mui.com), unless [decided otherwise](https://github.com/bcgov/wps/wiki/Frontend-Design-Decisions).

## Acknowledgments

Inspiration, code snippets, etc.

- [Create React App](https://github.com/facebook/create-react-app/)
- [Redux Toolkit - advanced tutorial](https://redux-toolkit.js.org/tutorials/advanced-tutorial/)

[![SonarCloud](https://sonarcloud.io/images/project_badges/sonarcloud-white.svg)](https://sonarcloud.io/dashboard?id=bcgov_wps)

Template copied from

- [DomPizzie](https://gist.github.com/DomPizzie/7a5ff55ffa9081f2de27c315f5018afc)
