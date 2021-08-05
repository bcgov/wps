declare module Cypress {
  interface Chainable {
    /**
     * Custom command to select the row weather station and check its value.
     * @example selectYearAndCheckValue('Full', 50)
     */
    selectFBAStationInDropdown(rowId: number, code: number | string): void
  }
}

Cypress.Commands.add(
  'selectFBAStationInDropdown',
  (rowId: number, code: number | string) => {
    if (typeof code === 'number') {
      return cy
        .getByTestId(`weather-station-dropdown-${rowId}`)
        .get('button[title="Open"]')
        .first()
        .click()
        .get('li')
        .contains(code)
        .click()
    }

    return cy
      .getByTestId(`weather-station-dropdown-${rowId}`)
      .find('input')
      .type(code)
      .type('{downarrow}')
      .type('{enter}')
  }
)
