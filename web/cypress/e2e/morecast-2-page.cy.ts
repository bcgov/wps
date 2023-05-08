import { MORE_CAST_2_ROUTE } from '../../src/utils/constants'

describe('More Cast 2 Page', () => {
  beforeEach(() => {
    cy.intercept('GET', 'api/fba/fire-centers', { fixture: 'fba/fire-centers.json' }).as('fireCenters')
    cy.intercept('GET', 'api/stations/groups').as('stationGroups')

    cy.visit(MORE_CAST_2_ROUTE)
  })

  it('Renders the initial page', () => {
    cy.getByTestId('station-group-dropdown').should('be.visible')
    cy.getByTestId('morecast2-data-grid').should('be.visible')
    cy.getByTestId('morecast2-station-panel').should('be.visible')
  })
})
