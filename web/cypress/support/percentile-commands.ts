declare module Cypress {
  interface Chainable {
    /**
     * Custom command to select the time range slider and check its value.
     * @example selectYearAndCheckValue('Full', 50)
     */
    selectYearInTimeRangeSlider(year: number | string, value: number): void

    /**
     * Custom command to request percentile results and check the request body.
     * @example requestPercentilesAndCheckRequestBody('@getPercentiles', { stations: [stationCode], year_range: { start: 1970, end: 2019 }, percentile: 90 })
     */
    requestPercentilesAndCheckRequestBody(alias: string, body: {}): void
  }
}

Cypress.Commands.add(
  'selectYearInTimeRangeSlider',
  (year: number | string, value: number) => {
    cy.get('.MuiSlider-markLabel')
      .contains(year)
      .click()
    cy.getByTestId('time-range-slider')
      .find('[type=hidden]')
      .should('have.value', value)
  }
)

Cypress.Commands.add(
  'requestPercentilesAndCheckRequestBody',
  (alias: string, body: {}) => {
    cy.getByTestId('calculate-percentiles-button').click()
    cy.wait(alias).then(interception => {
      expect(interception.response.body).to.eql(body)
    })
  }
)
