# Wildfire Predictive Services Web Application

## Description

Wildfire Predictive Services to support decision making in prevention, preparedness, response and recovery.

## Getting Started

### Dependencies

- [Node.js](https://nodejs.org/en/) - You’ll need to have Node >= 8.10 and npm >= 5.6 on your machine. You can use [nvm](https://github.com/nvm-sh/nvm#installation) (macOS/Linux) or [nvm-windows](https://github.com/coreybutler/nvm-windows#node-version-manager-nvm-for-windows) to switch Node versions between different projects.

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


## License

This project is licensed under the [Apache License, Version 2.0](https://github.com/bcgov/wps-web/blob/master/LICENSE).

## Acknowledgments

Inspiration, code snippets, etc.

- [Create React App](https://github.com/facebook/create-react-app/)
- [Redux Toolkit - advanced tutorial](https://redux-toolkit.js.org/tutorials/advanced-tutorial/)

Template copied from

- [DomPizzie](https://gist.github.com/DomPizzie/7a5ff55ffa9081f2de27c315f5018afc)
