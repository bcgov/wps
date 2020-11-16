/// <reference types="cypress" />

// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************
//
//
// -- This is a parent command --
// Cypress.Commands.add("login", (email, password) => { ... })
//
//
// -- This is a child command --
// Cypress.Commands.add("drag", { prevSubject: 'element'}, (subject, options) => { ... })
//
//
// -- This is a dual command --
// Cypress.Commands.add("dismiss", { prevSubject: 'optional'}, (subject, options) => { ... })
//
//
// -- This will overwrite an existing command --
// Cypress.Commands.overwrite("visit", (originalFn, url, options) => { ... })

// add new command to the existing Cypress interface

export {} // indicate that the file is a module

declare global {
  namespace Cypress {
    interface Chainable {
      /**
       * Custom command to select DOM element by data-testid attribute.
       * @example cy.getByTestId('error-message')
       */
      getByTestId(id: string): Chainable<Element>

      /**
       * Custom command to select a wx station by its code in the dropdown.
       * @example cy.selectStationByCode(322)
       */
      selectStationByCode(code: number): Chainable<Element>

      /**
       * Custom command to select ErrorMessage component and check the message.
       * @example cy.checkErrorMessage('Error occurred (while getting the calculation result).')
       */
      checkErrorMessage(msg: string): void
    }
  }
}
