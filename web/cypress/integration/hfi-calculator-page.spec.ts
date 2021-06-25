import { HFI_CALC_ROUTE } from '../../src/utils/constants'

describe('HFI Calculator Page', () => {
  beforeEach(() => {
    cy.intercept('GET', 'api/hfi-calc/daily*', { fixtures: 'hfi-calc/dailies.json' }).as('getDaily')
    cy.intercept('GET', 'api/hfi-calc/fire-centres', { fixture: 'hfi-calc/fire_centres.json' }).as('getFireCentres')
  })

  it('should display Daily View Table after landing on page', () => {
    cy.visit(HFI_CALC_ROUTE)
    cy.wait('@getFireCentres')
    cy.wait('@getDaily')
    cy.contains('HFI Calculator Daily View')
    cy.getByTestId('hfi-calc-daily-table')
  })

  it('should have at least 15 rows in Daily Table View', () => {
    cy.visit(HFI_CALC_ROUTE)
    cy.getByTestId('hfi-calc-daily-table')
      .find('tr')
      .should('have.length.at.least', 15)
  })
})
