import { HFI_CALC_ROUTE } from '../../src/utils/constants'

describe('HFI Calculator Page', () => {
  beforeEach(() => {
    cy.intercept('GET', 'api/hfi-calc/daily*', { fixture: 'hfi-calc/dailies.json' }).as('getDaily')
    cy.intercept('GET', 'api/hfi-calc/fire-centres', {
      fixture: 'hfi-calc/fire_centres.json'
    }).as('getFireCentres')
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

  it('should display weather results and intensity groups in Daily View Table', () => {
    cy.visit(HFI_CALC_ROUTE)
    cy.wait(['@getFireCentres', '@getDaily'])
    cy.getByTestId('zone-4-mean-intensity').contains(2)
    cy.getByTestId('239-hfi').contains(2655.5)
    cy.getByTestId('280-ros').contains(1.7)
    cy.getByTestId('239-fire-type').contains('S')
    cy.getByTestId('280-fire-type').contains('IC')
    cy.getByTestId('280-intensity-group').contains(3)
    cy.getByTestId('zone-0-mean-intensity').contains(2.4)
    cy.getByTestId('zone-0-mean-intensity').should($td => {
      const className = $td[0].className
      expect(className).to.match(/makeStyles-intensityGroupSolid2-/)
    })
  })
})
