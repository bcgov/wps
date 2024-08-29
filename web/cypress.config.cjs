const { defineConfig } = require('cypress');

module.exports = defineConfig({
  screenshotOnRunFailure: false,
  retries: 1,
  video: false,
  defaultCommandTimeout: 10000,
  e2e: {
    // specPattern: '**/fire-behaviour-advisory-calculator-page.cy.ts',
    // We've imported your old cypress plugins here.
    // You may want to clean this up later by importing these.
    setupNodeEvents(on, config) {
      require('@cypress/code-coverage/task')(on, config)
      return config

    },

    baseUrl: 'http://localhost:3030',
  },
});