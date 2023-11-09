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
import './fba-commands'
import './hfi-commands'
import '@cypress/code-coverage/support'

Cypress.Commands.add('getByTestId', (id: string) => {
  return cy.get(`[data-testid=${id}]`, { timeout: 15000 })
})

Cypress.Commands.add('selectStationInDropdown', (code: number | string) => {
  if (typeof code === 'number') {
    return cy
      .getByTestId('weather-station-dropdown')
      .get('button[title="Open"]')
      .click()
      .get('li')
      .contains(code)
      .click()
  }

  return cy.getByTestId('weather-station-dropdown').find('input').type(code).type('{downarrow}').type('{enter}')
})

Cypress.Commands.add('checkErrorMessage', (msg: string) => {
  cy.getByTestId('error-message').should('contain', msg)
})
