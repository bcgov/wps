declare namespace Cypress {
  interface Chainable {
    /**
     * Custom command to select a weather station and check its value.
     * @example selectFBAStationInDropdown(322)
     */
    selectFBAStationInDropdown(code: number | string, rowId: number): void

    /**
     * Custom command to select a fuel type and check its value.
     * @example selectFBAFuelTypeInDropdown('C1')
     */
    selectFBAFuelTypeInDropdown(fuelType: string, rowId: number): void

    /**
     * Custom command to set the grass cure percentage.
     * @example setFBAGrassCurePercentage('20')
     */
    setFBAGrassCurePercentage(grassCure: string, rowId: number): void

    /**
     * Custom command to set the wind speed.
     * @example setFBAWindSpeed('20')
     */
    setFBAWindSpeed(windSpeed: string, rowId: number): void

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

    /**
     * Custom command to expect the grass curing in a row.
     */
    grassCuringForRowShouldBe(grassCuring: string, rowId: number): void

    /**
     * Custom command to expect the windspeed in a row.
     */
    windSpeedForRowShouldBe(windSpeed: string, rowId: number): void

    /**
     * Custom command to expect the station code in a row.
     */
    stationCodeForRowShouldBe(stationCode: string, rowId: number): void

    /**
     * Custom command to expect the fuel type in a row.
     */
    fuelTypeForRowShouldBe(fuelType: string, rowId: number): void
  }
}

Cypress.Commands.add('selectFBAStationInDropdown', (code: number | string, rowId: number) => {
  return cy
    .getByTestId(`weather-station-dropdown-fba-${rowId}`)
    .find('input')
    .type(String(code))
    .type('{downarrow}')
    .type('{enter}')
})

Cypress.Commands.add('selectFBAFuelTypeInDropdown', (fuelType: string, rowId: number) => {
  return cy
    .getByTestId(`fuel-type-dropdown-fba-${rowId}`)
    .find('input')
    .type(fuelType)
    .type('{downarrow}')
    .type('{enter}')
})

Cypress.Commands.add('setFBAGrassCurePercentage', (grassCure: string, rowId: number) => {
  return cy.getByTestId(`grassCureInput-fba-${rowId}`).find('input').type(grassCure).type('{enter}')
})

Cypress.Commands.add('setFBAWindSpeed', (windSpeed: string, rowId: number) => {
  return cy.getByTestId(`windSpeedInput-fba-${rowId}`).find('input').type(windSpeed)
})

Cypress.Commands.add('setSelectedRow', () => {
  return cy.getByTestId(`selection-checkbox-fba`).click()
})

Cypress.Commands.add('rowCountShouldBe', (rowCount: number) => {
  return cy.getByTestId('fba-table-body').find('tr').should('have.length', rowCount)
})

Cypress.Commands.add('grassCuringForRowShouldBe', (grassCuring: string, rowId: number) => {
  return cy.getByTestId(`grassCureInput-fba-${rowId}`).find('input').should('have.value', grassCuring)
})

Cypress.Commands.add('windSpeedForRowShouldBe', (windSpeed: string, rowId: number) => {
  return cy.getByTestId(`windSpeedInput-fba-${rowId}`).find('input').should('have.value', windSpeed)
})

Cypress.Commands.add('stationCodeForRowShouldBe', (stationCode: string, rowId: number) => {
  return cy
    .getByTestId(`weather-station-dropdown-fba-${rowId}`)
    .find('input')
    .should($input => {
      expect($input.val()).to.include(stationCode)
    })
})

Cypress.Commands.add('fuelTypeForRowShouldBe', (fuelType: string, rowId: number) => {
  return cy
    .getByTestId(`fuel-type-dropdown-fba-${rowId}`)
    .find('input')
    .should($input => {
      expect($input.val()).to.include(fuelType.toUpperCase())
    })
})
