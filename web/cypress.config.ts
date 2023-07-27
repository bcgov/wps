import path from 'path'
import { defineConfig } from 'cypress'
import vitePreprocessor from 'cypress-vite'

export default defineConfig({
  screenshotOnRunFailure: false,
  video: false,
  defaultCommandTimeout: 100000,
  e2e: {
    // We've imported your old cypress plugins here.
    // You may want to clean this up later by importing these.
    setupNodeEvents(on, config) {
      on('file:preprocessor', vitePreprocessor(path.resolve(__dirname, './vite.config.ts')))
      return require('./cypress/plugins/index.js')(on, config)
    },
    baseUrl: 'http://localhost:3030'
  }
})
