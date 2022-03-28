import { HFI_CALC_ROUTE } from '../../src/utils/constants'

function interceptDaily(fixturePath: string) {
  // Inject an appropriate date into our mock data.
  cy.readFile(fixturePath).then(hfiRequest => {
    cy.intercept('POST', 'api/hfi-calc/', req => {
      hfiRequest['selected_prep_date'] = '2021-08-02'
      hfiRequest['start_date'] = '2021-08-02'
      hfiRequest['end_date'] = '2021-08-06'
      req.reply(hfiRequest)
    }).as('getHFIResults')
  })
}

function interceptLoad(fixturePath = 'hfi-calc/dailies-saved.json') {
  cy.intercept('GET', 'api/hfi-calc/fire_centre/*', {
    fixture: fixturePath
  }).as('loadHFIResults')
}

function interceptSetFireStarts() {
  cy.intercept(
    'POST',
    'api/hfi-calc/fire_centre/1/2021-08-02/planning_area/70/fire_starts/2021-08-02/fire_start_range/4',
    {
      fixture: 'hfi-calc/dailies-saved.json'
    }
  ).as('setFireStarts')
}

describe('HFI Calculator Page', () => {
  describe('first visit - no selected fire centre', () => {
    it('should show the select fire centre instructions', () => {
      cy.visit(HFI_CALC_ROUTE)
      cy.getByTestId('hfi-empty-fire-centre').should('be.visible')
    })
  })
  describe('prep period - saved', () => {
    beforeEach(() => {
      interceptLoad()
      cy.intercept('GET', 'api/hfi-calc/fire-centres', {
        fixture: 'hfi-calc/fire_centres.json'
      }).as('getFireCentres')
      cy.visit(HFI_CALC_ROUTE)
      cy.wait('@getFireCentres')
      cy.selectFireCentreInDropdown('Kamloops')
      cy.wait('@loadHFIResults')
    })
    it('save button should be disable', () => {
      // cypress/fixtures/hfi-calc/dailies-saved.json has "request_persist_success": true, save button should be looking at that.
      cy.getByTestId('save-button').should('be.disabled')
    })
    it('fire start dropdown triggers hfi set state request', () => {
      // Selecting a new fire start, should result in a new request to the server, that comes back with "request_persist_success": true, or
      // which should cause the save button to become disabled.
      interceptDaily('cypress/fixtures/hfi-calc/dailies.json')
      interceptSetFireStarts()
      cy.getByTestId('fire-starts-dropdown')
        .first()
        .find('input')
        .type('{downarrow}')
        .type('{downarrow}')
        .type('{enter}')
      cy.wait('@setFireStarts')
      cy.getByTestId('save-button').should('be.disabled')
    })
  })
  describe('all data exists', () => {
    beforeEach(() => {
      interceptLoad()
      cy.intercept('GET', 'api/hfi-calc/fire-centres', {
        fixture: 'hfi-calc/fire_centres.json'
      }).as('getFireCentres')
      cy.visit(HFI_CALC_ROUTE)
      cy.wait('@getFireCentres')
      cy.selectFireCentreInDropdown('Kamloops')
      cy.wait('@loadHFIResults')
      cy.getByTestId('daily-toggle-0').click({ force: true })
    })

    it('save button should be enabled', () => {
      // cypress/fixtures/hfi-calc/dailies.json does not have "request_persist_success": true, save button should be looking at that.
      cy.getByTestId('save-button').should('be.enabled')
    })

    it('should display Daily View Table after clicking on daily button', () => {
      cy.getByTestId('hfi-calc-daily-table')
    })

    it('should have at least 15 rows in Daily Table View', () => {
      cy.getByTestId('hfi-calc-daily-table').find('tr').should('have.length.at.least', 15)
    })

    it('should display weather results, intensity groups, & prep levels in Daily View Table', () => {
      cy.getByTestId('239-hfi').contains(25.8)
      cy.getByTestId('239-ros').contains(0.0)
      cy.getByTestId('239-1-hr-size').contains(0.0)
      cy.getByTestId('239-fire-type').contains('SUR')
      cy.getByTestId('239-intensity-group').contains(1)
      cy.getByTestId('zone-70-mean-intensity').contains(1)
      cy.getByTestId('daily-prep-level-70').contains(1)
      cy.getByTestId('daily-prep-level-70').should($td => {
        const className = $td[0].className
        expect(className).to.match(/makeStyles-prepLevel1-/)
      })
      cy.getByTestId('daily-prep-level-71').contains(3)
      cy.getByTestId('daily-prep-level-71').should($td => {
        expect($td[0].className).to.match(/makeStyles-prepLevel3-/)
      })
    })
  })
  describe('dailies data are missing', () => {
    beforeEach(() => {
      interceptLoad('hfi-calc/dailies-missing.json')
      cy.intercept('GET', 'api/hfi-calc/fire-centres', {
        fixture: 'hfi-calc/fire-centres-grass.json'
      }).as('getFireCentres')
      cy.visit(HFI_CALC_ROUTE)
      cy.selectFireCentreInDropdown('Kamloops')
      cy.wait('@getFireCentres')
      cy.wait('@loadHFIResults')
      cy.getByTestId('daily-toggle-0').click({ force: true })
    })
    it('should display error icon for mean intensity group in Daily View Table', () => {
      cy.getByTestId('306-ros').should('have.value', '')
      cy.getByTestId('306-hfi').should('have.value', '')
      cy.getByTestId('306-1-hr-size').should('have.value', '')
      cy.getByTestId('306-intensity-group').should('have.value', '')
      cy.getByTestId('zone-74-mig-error').scrollIntoView().should('be.visible')
    })
  })
  describe('high intensity', () => {
    beforeEach(() => {
      interceptLoad('hfi-calc/dailies-high-intensity.json')
      cy.intercept('GET', 'api/hfi-calc/fire-centres', {
        fixture: 'hfi-calc/fire-centres-minimal.json'
      }).as('getFireCentres')
      cy.visit(HFI_CALC_ROUTE)
      cy.selectFireCentreInDropdown('Kamloops')
      cy.wait('@getFireCentres')
      cy.wait('@loadHFIResults')
      cy.getByTestId('daily-toggle-0').click({ force: true })
    })
    it('should show highest intensity values for mean intensity group in Daily View Table', () => {
      cy.getByTestId('306-intensity-group').contains(5)
      cy.getByTestId('zone-74-mean-intensity').contains(5)
    })
  })
})
