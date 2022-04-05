/* eslint-disable @typescript-eslint/no-namespace */
declare namespace Cypress {
  interface Chainable {
    /**
     * Custom command to select a fire centre from the dropdown menu.
     * @example selectFBAStationInDropdown(322)
     */
    selectFireCentreInDropdown(name: string): void
  }
}

Cypress.Commands.add('selectFireCentreInDropdown', (name: string) => {
  return cy
    .getByTestId(`fire-centre-dropdown`)
    .find('input')
    .clear()
    .type(name)
    .type('{downarrow}')
    .type('{enter}')
})
