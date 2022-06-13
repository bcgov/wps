import { HFI_CALC_ROUTE } from '../../src/utils/constants'

function interceptSelectStationTrue(
  fire_centre: number,
  start_date: string,
  end_date: string,
  planning_area: number,
  code: number
) {
  cy.intercept(
    'POST',
    `api/hfi-calc/fire_centre/${fire_centre}/${start_date}/${end_date}/planning_area/${planning_area}/station/${code}/selected/true`,
    {
      fixture: 'hfi-calc/dailies-saved.json'
    }
  ).as('selectStationTrue')
}

function interceptGetPrepPeriod(fire_centre: number, start_date: string, end_date: string) {
  cy.intercept('GET', `api/hfi-calc/fire_centre/${fire_centre}/${start_date}/${end_date}`, {
    fixture: 'hfi-calc/dailies-saved.json'
  }).as('getPrepPeriod')
}

function interceptSetFuelType(
  fire_centre: number,
  start_date: string,
  end_date: string,
  planning_area: number,
  code: number,
  fuel_type_id: number
) {
  cy.intercept(
    'POST',
    `api/hfi-calc/fire_centre/${fire_centre}/${start_date}/${end_date}/planning_area/${planning_area}/station/${code}/fuel_type/${fuel_type_id}`,
    {
      fixture: 'hfi-calc/dailies-saved.json'
    }
  ).as('setFuelType')
}

function interceptSelectStationFalse(
  fire_centre: number,
  start_date: string,
  end_date: string,
  planning_area: number,
  code: number
) {
  cy.intercept(
    'POST',
    `api/hfi-calc/fire_centre/${fire_centre}/${start_date}/${end_date}/planning_area/${planning_area}/station/${code}/selected/false`,
    {
      fixture: 'hfi-calc/dailies-disable-station.json'
    }
  ).as('selectStationFalse')
}

function interceptLoad(fixturePath: string, fireCentresFixturePath = 'hfi-calc/fire_centres.json') {
  cy.intercept('GET', 'api/hfi-calc/fire_centre/*', {
    fixture: fixturePath
  }).as('loadHFIResults')
  cy.intercept('GET', 'api/hfi-calc/fire-centres', {
    fixture: fireCentresFixturePath
  }).as('getFireCentres')
  cy.intercept('GET', 'api/hfi-calc/fuel_types', {
    fixture: 'hfi-calc/fuel_types.json'
  }).as('getFuelTypes')
}

function interceptSetFireStarts(
  fire_centre: number,
  start_date: string,
  end_date: string,
  planning_area: number,
  prep_date: string,
  fire_start_range_id: number
) {
  cy.intercept(
    'POST',
    `api/hfi-calc/fire_centre/${fire_centre}/${start_date}/${end_date}/planning_area/${planning_area}/fire_starts/${prep_date}/fire_start_range/${fire_start_range_id}`,
    {
      fixture: 'hfi-calc/dailies-saved.json'
    }
  ).as('setFireStarts')
}

function interceptGetReadyStates(fire_centre: number, start_date: string, end_date: string) {
  cy.intercept('GET', `api/hfi-calc/fire_centre/${fire_centre}/${start_date}/${end_date}/ready`, {
    fixture: 'hfi-calc/ready-states.json'
  }).as('getReadyStates')
}

function interceptToggleReadyState(fire_centre: number, planning_area: number, start_date: string, end_date: string) {
  cy.intercept(
    'POST',
    `api/hfi-calc/fire_centre/${fire_centre}/planning_area/${planning_area}/${start_date}/${end_date}/ready`
  ).as('toggleReadyState')
}

function interceptDownload(start_date: string, end_date: string) {
  cy.intercept('GET', `api/hfi-calc/fire_centre/1/${start_date}/${end_date}/pdf`).as('downloadPDF')
}

describe('HFI Calculator Page', () => {
  const start_date = '2021-08-02'
  const end_date = '2021-08-06'
  describe('first visit - no selected fire centre', () => {
    it('should show the select fire centre instructions', () => {
      cy.visit(HFI_CALC_ROUTE)
      cy.getByTestId('hfi-empty-fire-centre').should('be.visible')
    })
  })
  describe('prep period - saved', () => {
    beforeEach(() => {
      interceptLoad('hfi-calc/dailies-saved.json')
      interceptGetReadyStates(1, start_date, end_date)
      cy.visit(HFI_CALC_ROUTE)
      cy.wait('@getFireCentres')
      cy.wait('@getFuelTypes')
      cy.selectFireCentreInDropdown('Kamloops')
      cy.wait('@loadHFIResults')
    })
    it('toggle station works', () => {
      // Click on a station, check that it's not checked. Click it again
      // check that it's checked.
      interceptSelectStationFalse(1, start_date, end_date, 70, 239)
      cy.getByTestId('select-station-239').click({ force: true })
      cy.wait('@selectStationFalse')
      cy.getByTestId('select-station-239').find('input').should('be.not.checked')
      interceptSelectStationTrue(1, start_date, end_date, 70, 239)
      cy.getByTestId('select-station-239').click({ force: true })
      cy.wait('@selectStationTrue')
      cy.getByTestId('select-station-239').find('input').should('be.checked')
      cy.getByTestId('hfi-success-alert').should('exist')
    })
    it('prep period should send a new request to the server', () => {
      interceptGetPrepPeriod(1, '2021-08-03', '2021-08-07')
      // Open date range picker modal
      cy.getByTestId('date-range-picker-text-field').click({ force: true })

      // Reset date range
      cy.getByTestId('date-range-reset-button').click({ force: true })

      // Click to set a new start date
      cy.getByTestId('day-2021-08-03').click()

      // Click to set a new end date
      cy.getByTestId('day-2021-08-07').click()

      // Close modal
      cy.getByTestId('date-range-picker-wrapper').type('{esc}')

      cy.wait('@getPrepPeriod')

      cy.getByTestId('hfi-success-alert').should('not.exist')
    })
    it('new fire starts should send a new request to the server', () => {
      // Selecting a new fire start, should result in a new request to the server.
      interceptSetFireStarts(1, '2021-08-02', '2021-08-06', 70, '2021-08-02', 4)
      cy.getByTestId('fire-starts-dropdown')
        .first()
        .find('input')
        .type('{downarrow}')
        .type('{downarrow}')
        .type('{enter}')
      cy.wait('@setFireStarts')
      cy.getByTestId('hfi-success-alert').should('exist')
    })
    it('set fuel type should send a request to the server', () => {
      interceptSetFuelType(1, '2021-08-02', '2021-08-06', 70, 239, 3)
      cy.getByTestId('fuel-type-dropdown')
        .first()
        .find('input')
        .type('{downarrow}', { force: true })
        .type('{downarrow}', { force: true })
        .type('{enter}', { force: true })
      cy.wait('@setFuelType')
      cy.getByTestId('hfi-success-alert').should('exist')
    })
    it('should switch the tab to prep period from a daily tab when a different fire centre is selected', () => {
      cy.getByTestId('daily-toggle-1').click({ force: true })
      cy.getByTestId('hfi-calc-daily-table').should('be.visible')
      cy.selectFireCentreInDropdown('Coastal')
      cy.getByTestId('hfi-calc-daily-table').should('not.exist')
      cy.getByTestId('hfi-calc-weekly-table').should('be.visible')
    })
  })
  describe('ready states', () => {
    beforeEach(() => {
      interceptLoad('hfi-calc/dailies-saved.json')
      interceptGetReadyStates(1, start_date, end_date)
      interceptToggleReadyState(1, 70, start_date, end_date)
      cy.visit(HFI_CALC_ROUTE)
      cy.wait('@getFireCentres')
      cy.wait('@getFuelTypes')
      cy.selectFireCentreInDropdown('Kamloops')
      cy.wait('@loadHFIResults')
      cy.wait('@getReadyStates')
    })
    it('should toggle off ready state when a station is unselected', () => {
      interceptSelectStationFalse(1, start_date, end_date, 70, 239)
      cy.getByTestId('select-station-239').click({ force: true })
      cy.wait('@selectStationFalse')
      cy.getByTestId('select-station-239').find('input').should('be.not.checked')
      cy.getByTestId('hfi-success-alert').should('exist')
      cy.wait('@toggleReadyState')
    })
    it('should toggle off ready state when fire starts is changed', () => {
      interceptSetFireStarts(1, '2021-08-02', '2021-08-06', 70, '2021-08-02', 4)
      cy.getByTestId('fire-starts-dropdown')
        .first()
        .find('input')
        .type('{downarrow}')
        .type('{downarrow}')
        .type('{enter}')
      cy.wait('@setFireStarts')
      cy.getByTestId('hfi-success-alert').should('exist')
      cy.wait('@toggleReadyState')
    })
    it('should toggle off ready state when fuel type is changed', () => {
      interceptSetFuelType(1, '2021-08-02', '2021-08-06', 70, 239, 3)
      cy.getByTestId('fuel-type-dropdown')
        .first()
        .find('input')
        .type('{downarrow}', { force: true })
        .type('{downarrow}', { force: true })
        .type('{enter}', { force: true })
      cy.wait('@setFuelType')
      cy.getByTestId('hfi-success-alert').should('exist')
      cy.wait('@toggleReadyState')
    })
  })
  describe('all data exists', () => {
    beforeEach(() => {
      interceptLoad('hfi-calc/dailies.json')
      cy.visit(HFI_CALC_ROUTE)
      cy.wait('@getFireCentres')
      cy.wait('@getFuelTypes')
      cy.selectFireCentreInDropdown('Kamloops')
      cy.wait('@loadHFIResults')
      cy.getByTestId('daily-toggle-0').click({ force: true })
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

    it('download should hit pdf download url', () => {
      interceptDownload('2021-08-02', '2021-08-06')
      cy.getByTestId('download-pdf-button').click({ force: true })
      cy.wait('@downloadPDF')
    })
  })
  describe('dailies data are missing', () => {
    beforeEach(() => {
      interceptLoad('hfi-calc/dailies-missing.json')
      cy.visit(HFI_CALC_ROUTE)
      cy.selectFireCentreInDropdown('Kamloops')
      cy.wait('@getFireCentres')
      cy.wait('@getFuelTypes')
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
      interceptLoad('hfi-calc/dailies-high-intensity.json', 'hfi-calc/fire-centres-minimal.json')
      cy.visit(HFI_CALC_ROUTE)
      cy.selectFireCentreInDropdown('Kamloops')
      cy.wait('@getFireCentres')
      cy.wait('@getFuelTypes')
      cy.wait('@loadHFIResults')
      cy.getByTestId('daily-toggle-0').click({ force: true })
    })
    it('should show highest intensity values for mean intensity group in Daily View Table', () => {
      cy.getByTestId('306-intensity-group').contains(5)
      cy.getByTestId('zone-74-mean-intensity').contains(5)
    })
  })
  describe('hfi api endpoint error handling', () => {
    beforeEach(() => {
      interceptLoad('hfi-calc/dailies.json')
      cy.visit(HFI_CALC_ROUTE)
      cy.wait('@getFireCentres')
      cy.wait('@getFuelTypes')
      cy.selectFireCentreInDropdown('Kamloops')
      cy.wait('@loadHFIResults')
    })
    it('should notify user if endpoint request fails with 500', () => {
      cy.intercept('GET', 'api/hfi-calc/fire_centre/*', {
        statusCode: 500
      }).as('failedLoadHFI')
      cy.selectFireCentreInDropdown('Kamloops')
      cy.getByTestId('hfi-error-alert').should('be.visible')
    })
    it('should notify user if endpoint request fails with 401', () => {
      cy.intercept('GET', 'api/hfi-calc/fire_centre/*', {
        statusCode: 401
      }).as('failedLoadHFI')
      cy.selectFireCentreInDropdown('Kamloops')
      cy.getByTestId('hfi-error-alert').should('be.visible')
    })
    it('should notify user if endpoint request fails with 404', () => {
      cy.intercept('GET', 'api/hfi-calc/fire_centre/*', {
        statusCode: 404
      }).as('failedLoadHFI')
      cy.selectFireCentreInDropdown('Kamloops')
      cy.getByTestId('hfi-error-alert').should('be.visible')
    })
  })
  describe('fire centres api endpoint error handling', () => {
    it('should notify user if endpoint request fails with 500', () => {
      cy.intercept('GET', 'api/hfi-calc/fire-centres', {
        statusCode: 500
      }).as('failedFireCentres')
      cy.visit(HFI_CALC_ROUTE)
      cy.selectFireCentreInDropdown('Kamloops')
      cy.getByTestId('hfi-error-alert').should('be.visible')
    })
    it('should notify user if endpoint request fails with 401', () => {
      cy.intercept('GET', 'api/hfi-calc/fire-centres', {
        statusCode: 401
      }).as('failedFireCentres')
      cy.visit(HFI_CALC_ROUTE)
      cy.selectFireCentreInDropdown('Kamloops')
      cy.getByTestId('hfi-error-alert').should('be.visible')
    })
    it('should notify user if endpoint request fails with 404', () => {
      cy.intercept('GET', 'api/hfi-calc/fire-centres', {
        statusCode: 404
      }).as('failedFireCentres')
      cy.visit(HFI_CALC_ROUTE)
      cy.selectFireCentreInDropdown('Kamloops')
      cy.getByTestId('hfi-error-alert').should('be.visible')
    })
  })
})
