const { defineConfig } = require('cypress');

module.exports = defineConfig({
  allowCypressEnv: false,
  screenshotOnRunFailure: false,
  retries: 1,
  video: false,
  defaultCommandTimeout: 10000,
  e2e: {
    setupNodeEvents(on, config) {
      require('@cypress/code-coverage/task')(on, config)
      return config

    },
    baseUrl: 'http://localhost:3030',
  },
});