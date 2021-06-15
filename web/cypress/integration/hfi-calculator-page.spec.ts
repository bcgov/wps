import { HFI_CALC_ROUTE } from '../../src/utils/constants'

describe('HFI Calculator Page', () => {
  beforeEach(() => {
    cy.intercept('GET', 'api/hfi-calc/fire-centres', { fixture: 'hfi-calc/stations.json' }).as('getFireCentres')
  })

  it('should display Daily View Table after landing on page', () => {
    cy.visit(HFI_CALC_ROUTE)
    cy.contains('HFI Calculator Daily View')
    cy.wait('@getFireCentres')
    cy.getByTestId('hfi-calc-daily-table')
  })

  it('should have a fire centre label as the first row of the Daily View Table', () => {
    cy.visit(HFI_CALC_ROUTE)
    cy.get('tr')
      .eq(1)
      .should('contain', 'Fire Centre')
  })

  it('should have at least 15 rows in Daily Table View', () => {
    cy.visit(HFI_CALC_ROUTE)
    cy.getByTestId('hfi-calc-daily-table')
      .find('tr')
      .should('have.length.at.least', 15)
  })
})
