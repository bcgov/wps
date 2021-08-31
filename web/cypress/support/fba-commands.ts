declare module Cypress {
  interface Chainable {
    /**
     * Custom command to select a weather station and check its value.
     * @example selectFBAStationInDropdown(322)
     */
    selectFBAStationInDropdown(code: number | string): void

    /**
     * Custom command to select a fuel type and check its value.
     * @example selectFBAFuelTypeInDropdown('C1')
     */
    selectFBAFuelTypeInDropdown(fuelType: string): void

    /**
     * Custom command to set the grass cure percentage.
     * @example setFBAGrassCurePercentage('20')
     */
    setFBAGrassCurePercentage(grassCure: string): void

    /**
     * Custom command to set the wind speed.
     * @example setFBAWindSpeed('20')
     */
    setFBAWindSpeed(windSpeed: string): void

    /**
     * Custom command to set the date.
     * @example setDate('2021-08-05')
     */
    setDate(date: string): void

    /**
     * Custom command to select a row. Only works for single row.
     * @example setSelectedRow()
     */
    setSelectedRow(): void

    /**
     * Custom command to expect number of rows.
     * @example rowCountShouldBe(0)
     */
    rowCountShouldBe(rowCount: number): void
  }
}

Cypress.Commands.add('selectFBAStationInDropdown', (code: number | string) => {
  if (typeof code === 'number') {
    return cy
      .getByTestId('weather-station-dropdown-fba')
      .get('button[title="Open"]')
      .first()
      .click()
      .get('li')
      .contains(code)
      .click()
  }

  return cy
    .getByTestId('weather-station-dropdown-fba')
    .find('input')
    .type(code)
    .type('{downarrow}')
    .type('{enter}')
})

Cypress.Commands.add('selectFBAFuelTypeInDropdown', (fuelType: string) => {
  return cy
    .getByTestId('fuel-type-dropdown-fba')
    .find('input')
    .type(fuelType)
    .type('{downarrow}')
    .type('{enter}')
})

Cypress.Commands.add('setFBAGrassCurePercentage', (grassCure: string) => {
  return cy
    .getByTestId('grassCureInput-fba')
    .find('input')
    .type(grassCure)
    .type('{enter}')
})

Cypress.Commands.add('setFBAWindSpeed', (windSpeed: string) => {
  return cy
    .getByTestId(`windSpeedInput-fba`)
    .find('input')
    .type(windSpeed)
})

Cypress.Commands.add('setDate', (date: string) => {
  return cy
    .getByTestId('date-of-interest-picker')
    .find('input')
    .type(date)
})

Cypress.Commands.add('setSelectedRow', () => {
  return cy.getByTestId(`selection-checkbox-fba`).click()
})

Cypress.Commands.add('rowCountShouldBe', (rowCount: number) => {
  return cy
    .getByTestId('fba-table-body')
    .find('tr')
    .should('have.length', rowCount)
})
