import { HFI_CALC_ROUTE } from '../../src/utils/constants'

describe('HFI Calculator Page', () => {
  describe('all data exists', () => {
    beforeEach(() => {
      cy.intercept('GET', 'api/hfi-calc/daily*', { fixture: 'hfi-calc/dailies.json' }).as(
        'getDaily'
      )
      cy.intercept('GET', 'api/hfi-calc/fire-centres', {
        fixture: 'hfi-calc/fire_centres.json'
      }).as('getFireCentres')
    })

    it('should display Daily View Table after landing on page', () => {
      cy.visit(HFI_CALC_ROUTE)
      cy.wait('@getFireCentres')
      cy.wait('@getDaily')
      cy.getByTestId('hfi-calc-daily-table')
    })

    it('should have at least 15 rows in Daily Table View', () => {
      cy.visit(HFI_CALC_ROUTE)
      cy.getByTestId('hfi-calc-daily-table').find('tr').should('have.length.at.least', 15)
    })

    it('should display weather results, intensity groups, & prep levels in Daily View Table', () => {
      cy.visit(HFI_CALC_ROUTE)
      cy.wait(['@getFireCentres', '@getDaily'])
      cy.getByTestId('239-hfi').contains(2655.5)
      cy.getByTestId('280-ros').contains(1.7)
      cy.getByTestId('239-1-hr-size').contains(0.5)
      cy.getByTestId('239-fire-type').contains('S')
      cy.getByTestId('280-fire-type').contains('IC')
      cy.getByTestId('280-intensity-group').contains(3)
      cy.getByTestId('zone-1-mean-intensity').contains(2.4)
      cy.getByTestId('zone-1-mean-intensity').should($td => {
        const className = $td[0].className
        expect(className).to.match(/makeStyles-intensityGroupSolid2-/)
      })
      cy.getByTestId('daily-prep-level-0').contains(1)
      cy.getByTestId('daily-prep-level-0').should($td => {
        const className = $td[0].className
        expect(className).to.match(/makeStyles-prepLevel1-/)
      })
      cy.getByTestId('daily-prep-level-2').contains(3)
      cy.getByTestId('daily-prep-level-2').should($td => {
        expect($td[0].className).to.match(/makeStyles-prepLevel3-/)
      })
    })

    it('should allow date of interest to be changed with DatePicker component', () => {
      cy.visit(HFI_CALC_ROUTE)
      cy.wait(['@getFireCentres', '@getDaily'])
      cy.getByTestId('date-of-interest-picker').type('2021-07-22')
      cy.getByTestId('hfi-calc-daily-table').click({ force: true })
      cy.wait(['@getFireCentres', '@getDaily'])
    })
  })
  describe('dailies data are missing', () => {
    beforeEach(() => {
      cy.intercept('GET', 'api/hfi-calc/daily*', {
        fixture: 'hfi-calc/dailies-missing.json'
      }).as('getDaily')
      cy.intercept('GET', 'api/hfi-calc/fire-centres', {
        fixture: 'hfi-calc/fire-centres-grass.json'
      }).as('getFireCentres')
    })
    it('should display error icon for mean intensity group in Daily View Table', () => {
      cy.visit(HFI_CALC_ROUTE)
      cy.wait(['@getFireCentres', '@getDaily'])
      cy.getByTestId('306-ros').should('have.value', '')
      cy.getByTestId('306-hfi').should('have.value', '')
      cy.getByTestId('306-1-hr-size').should('have.value', '')
      cy.getByTestId('306-intensity-group').should('have.value', '')
      cy.getByTestId('zone-1-mig-error').scrollIntoView().should('be.visible')
    })
  })
  describe('high intensity', () => {
    beforeEach(() => {
      cy.intercept('GET', 'api/hfi-calc/daily*', {
        fixture: 'hfi-calc/dailies-high-intensity.json'
      }).as('getDaily')
      cy.intercept('GET', 'api/hfi-calc/fire-centres', {
        fixture: 'hfi-calc/fire-centres-minimal.json'
      }).as('getFireCentres')
    })
    it('should show highest intensity values for mean intensity group in Daily View Table', () => {
      cy.visit(HFI_CALC_ROUTE)
      cy.wait(['@getFireCentres', '@getDaily'])
      cy.getByTestId('306-intensity-group').contains(5)
      cy.getByTestId('zone-1-mean-intensity').contains(5)
      cy.getByTestId('zone-1-mean-intensity').should($td => {
        const className = $td[0].className
        expect(className).to.match(/makeStyles-intensityGroupSolid5-/)
      })
    })
  })
})
