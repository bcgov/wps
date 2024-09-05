import { FIRE_BEHAVIOUR_ADVISORY_ROUTE } from '../../src/utils/constants'

describe('Fire Behaviour Advisory Page', () => {
  beforeEach(() => {
    cy.intercept('GET', 'api/stations/*', { fixture: 'weather-stations.json' }).as('getStations')
    cy.intercept('GET', 'api/fba/fire-centers', { fixture: 'fba/fire-centers.json' }).as('fireCenters')

    cy.intercept(
      {
        hostname: 'maps.gov.bc.ca'
      },
      { fixture: 'fba/vectors.json' }
    ).as('getVectors')

    cy.visit(FIRE_BEHAVIOUR_ADVISORY_ROUTE)
  })

  it('Renders the initial page', () => {
    cy.getByTestId('fire-center-dropdown').should('be.visible')
    cy.getByTestId('fba-map').should('be.visible')
  })

  it.skip('Sets the fireCenter in local storage when it is changed in dropdown', () => {
    cy.wait('@getStations')
    cy.getByTestId('fire-center-dropdown')
      .click()
      .type('{downArrow}')
      .type('{enter}')
      .should(() => {
        expect(localStorage.getItem('preferredFireCenter')).to.equal('50')
      })
  })

  it('Has the preferredFireCenter in local storage not set if a center has not been selected before', () => {
    cy.getByTestId('fire-center-dropdown')
      .contains('Select Fire Center')
      .should(() => {
        expect(localStorage.getItem('preferredFireCenter')).to.be.null
      })
  })
})
