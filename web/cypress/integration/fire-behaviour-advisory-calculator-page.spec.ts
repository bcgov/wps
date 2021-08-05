import { FIRE_BEHAVIOR_CALC_ROUTE } from '../../src/utils/constants'

describe('FireBAT Calculator Page', () => {
  describe('Weather station dropdown', () => {
    xit('Renders error message when fetching stations failed', () => {
      cy.intercept('GET', 'api/stations/*', {
        statusCode: 404,
        response: 'error'
      }).as('getStations')
      cy.visit(FIRE_BEHAVIOR_CALC_ROUTE)

      cy.wait('@getStations')
      cy.checkErrorMessage('Error occurred (while fetching weather stations).')
    })

    it('Can select station if successfully received stations', () => {
      cy.intercept('GET', 'api/stations/*', { fixture: 'weather-stations.json' }).as('getStations')
      cy.visit(FIRE_BEHAVIOR_CALC_ROUTE)

      cy.getByTestId('add-row').click()

      cy.wait('@getStations')

      const stationCode = 322
      cy.selectFBAStationInDropdown(0, stationCode)

      // Check if the url query has been changed
      cy.url().should('contain', `s=${stationCode}`)
    })
  })
})
