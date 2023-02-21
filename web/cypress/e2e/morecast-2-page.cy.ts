import { MORE_CAST_2_ROUTE } from '../../src/utils/constants'

describe('More Cast 2 Page', () => {
  beforeEach(() => {
    cy.intercept('GET', 'api/fba/fire-centers', { fixture: 'fba/fire-centers.json' }).as('fireCenters')

    cy.visit(MORE_CAST_2_ROUTE)
  })

  it('Renders the initial page', () => {
    cy.getByTestId('fire-center-dropdown').should('be.visible')
    cy.getByTestId('morecast2-data-grid').should('be.visible')
    cy.getByTestId('morecast2-station-panel').should('be.visible')
    cy.getByTestId('weather-model-dropdown').should('be.visible')
  })

  it('Writes typed fire center to local storage', () => {
    cy.clearLocalStorage()
    cy.getByTestId('fire-center-dropdown').should('be.visible').type('North').type('{downarrow}').type('{enter}')
    cy.getAllLocalStorage().then(result => {
      expect(result).to.deep.equal({
        'http://localhost:3030': {
          preferredMoreCast2FireCenter: '42'
        }
      })
    })
  })

  it('Writes clicked fire center to local storage', () => {
    cy.clearLocalStorage()
    cy.getByTestId('fire-center-dropdown').should('be.visible').click().get('li[data-option-index="1"').click()
    cy.getAllLocalStorage().then(result => {
      expect(result).to.deep.equal({
        'http://localhost:3030': {
          preferredMoreCast2FireCenter: '60'
        }
      })
    })
  })
})
