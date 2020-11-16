// ***********************************************************
// This example support/index.js is processed and
// loaded automatically before your test files.
//
// This is a great place to put global configuration and
// behavior that modifies Cypress.
//
// You can change the location of this file or turn off
// automatically serving support files with the
// 'supportFile' configuration option.
//
// You can read more here:
// https://on.cypress.io/configuration
// ***********************************************************

// Import commands.js using ES2015 syntax:
import './commands'
import './percentile-commands'
import '@cypress/code-coverage/support'

Cypress.Commands.add('getByTestId', (id: string) => {
  return cy.get(`[data-testid=${id}]`)
})

Cypress.Commands.add('selectStationByCode', (code: number) => {
  return cy
    .getByTestId('weather-station-dropdown')
    .click()
    .get('li')
    .contains(code)
    .click()
})

Cypress.Commands.add('checkErrorMessage', (msg: string) => {
  cy.getByTestId('error-message').should('contain', msg)
})

/* Increase this if needed to slow down the test speed */
const COMMAND_DELAY = 0

for (const command of [
  'visit',
  'click',
  'trigger',
  'type',
  'clear',
  'reload',
  'contains'
]) {
  Cypress.Commands.overwrite(command, (originalFn, ...args) => {
    const origVal = originalFn(...args)

    return new Promise(resolve => {
      setTimeout(() => {
        resolve(origVal)
      }, COMMAND_DELAY)
    })
  })
}
