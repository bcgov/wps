declare module Cypress {
  interface Chainable {
    /**
     * Custom command to select the row weather station and check its value.
     * @example selectFBAStationInDropdown(0, 322)
     */
    selectFBAStationInDropdown(rowId: number, code: number | string): void

    /**
     * Custom command to select the row fuel type and check its value.
     * @example selectFBAFuelTypeInDropdown(0, 'C1')
     */
    selectFBAFuelTypeInDropdown(rowId: number, fuelType: string): void

    /**
     * Custom command to set the grass cure percentage.
     * @example setFBAGrassCurePercentage(0, '20')
     */
    setFBAGrassCurePercentage(rowId: number, grassCure: string): void

    /**
     * Custom command to set the wind speed.
     * @example setFBAWindSpeed(0, '20')
     */
    setFBAWindSpeed(rowId: number, grassCure: string): void

    /**
     * Custom command to set the date.
     * @example setDate('2021-08-05')
     */
    setDate(date: string): void
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

Cypress.Commands.add('selectFBAFuelTypeInDropdown', (rowId: number, fuelType: string) => {
  return cy
    .getByTestId(`fuel-type-dropdown-${rowId}`)
    .find('input')
    .type(fuelType)
    .type('{downarrow}')
    .type('{enter}')
})

Cypress.Commands.add('setFBAGrassCurePercentage', (rowId: number, grassCure: string) => {
  return cy
    .getByTestId(`grassCureInput-${rowId}`)
    .find('input')
    .type(grassCure)
    .type('{enter}')
})

Cypress.Commands.add('setFBAWindSpeed', (rowId: number, windSpeed: string) => {
  return cy
    .getByTestId(`windSpeedInput-${rowId}`)
    .find('input')
    .type(windSpeed)
})

Cypress.Commands.add('setDate', (date: string) => {
  return cy
    .getByTestId('date-of-interest-picker')
    .find('input')
    .type(date)
})
