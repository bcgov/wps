import { NOT_AVAILABLE } from '../../src/utils/strings'
import { PERCENTILE_CALC_ROUTE } from '../../src/utils/constants'
import { stationCodeQueryKey } from '../../src/utils/url'

describe('Percentile Calculator Page', () => {
  beforeEach(() => {
    cy.server()
  })

  describe('Weather station dropdown', () => {
    it('Renders error message when fetching stations failed', () => {
      cy.visit(PERCENTILE_CALC_ROUTE)
      cy.getByTestId('disclaimer-accept-button').click()
      cy.checkErrorMessage('Error occurred (while fetching weather stations).')
    })

    it('Can select & deselect stations if successfully received stations', () => {
      cy.route('GET', 'api/stations/', 'fixture:weather-stations.json').as('getStations')
      cy.visit(PERCENTILE_CALC_ROUTE)
      cy.getByTestId('disclaimer-accept-button').click()
      cy.wait('@getStations')

      // Select a station with its name
      cy.selectStationInDropdown('AFTON')

      // Deselect the selected station
      cy.get('.MuiChip-deleteIcon').click()

      // Select multiple stations in the dropdown and check if only 3 stations were selected
      const stationCodes = [1275, 322, 209, 838]
      stationCodes.forEach(code => {
        cy.selectStationInDropdown(code)
      })
      cy.get('.MuiChip-deletable').should('have.length', 3)

      // Check if the url query has been changed
      cy.getByTestId('calculate-percentiles-button').click()
      cy.url().should('contain', `${stationCodeQueryKey}=${stationCodes.slice(0, 3).join(',')}`)
    })

    it('Should let users know if there were invalid weather stations', () => {
      const invalidCodes = [1, 999]
      cy.route('GET', 'api/stations/', 'fixture:weather-stations.json').as('getStations')
      cy.visit(`${PERCENTILE_CALC_ROUTE}?${stationCodeQueryKey}=${invalidCodes.join(',')}`)
      cy.getByTestId('disclaimer-accept-button').click()

      // Remove the invalid codes from the dropdown and check if the error message is gone
      cy.getByTestId('error-message').contains('Invalid weather station code(s) detected.')
      cy.getByTestId('weather-station-dropdown').contains(`Invalid (${invalidCodes[0]})`)
      cy.get('.MuiChip-deleteIcon').first().click() // prettier-ignore
      cy.getByTestId('weather-station-dropdown').contains(`Invalid (${invalidCodes[1]})`)
      cy.get('.MuiChip-deleteIcon').click()
      cy.getByTestId('error-message').should('not.contain', 'Invalid weather station code(s) detected.')
    })
  })

  describe('For analytics', () => {
    it('Some DOM elements should exist with IDs', () => {
      cy.visit(PERCENTILE_CALC_ROUTE)
      cy.get('#disclaimer-accept-button').click()

      cy.get('#reset-percentiles-button')
      cy.get('#weather-station-dropdown')
      cy.get('#launch-map-link')
      cy.get('#contact-link')
      cy.get('#calculate-percentiles-button')
    })
  })

  describe('Other inputs', () => {
    beforeEach(() => {
      cy.route('GET', 'api/stations/', 'fixture:weather-stations.json')
      cy.visit(PERCENTILE_CALC_ROUTE)
      cy.getByTestId('disclaimer-accept-button').click()
    })

    it('Time range slider can select the range between 10 and 50', () => {
      cy.getByTestId('time-range-slider')
        .find('[type=hidden]')
        .should('have.value', 10) // default value

      // Select 20 year and check if reflected
      cy.selectYearInTimeRangeSlider(20, 20)

      // Select Full year and check if reflected
      cy.selectYearInTimeRangeSlider('Full', 50)

      // Should do nothing if 0 was selected
      cy.selectYearInTimeRangeSlider(0, 50)

      const stationCode = 838
      cy.selectStationInDropdown(stationCode)

      cy.route('POST', 'api/percentiles/').as('getPercentiles')
      cy.requestPercentilesAndCheckRequestBody('@getPercentiles', {
        stations: [stationCode],
        year_range: { start: 1970, end: 2019 }, // Full was selected
        percentile: 90
      })
    })

    it('Percentile textfield should have a value of 90', () => {
      cy.getByTestId('percentile-textfield')
        .find('[type=text]')
        .should('have.value', 90)
        .should('have.class', 'Mui-disabled')
    })
  })

  describe('Calculation result', () => {
    beforeEach(() => {
      cy.route('GET', 'api/stations/', 'fixture:weather-stations.json').as('getStations')
      cy.visit(PERCENTILE_CALC_ROUTE, {
        onBeforeLoad: (win: any) => {
          win._mtm = { push: () => {} } // mock Matomo object
        }
      })
      cy.getByTestId('disclaimer-accept-button').click()
    })

    it('Failed due to network error', () => {
      // Calculate button should be disabled if no stations selected
      cy.getByTestId('calculate-percentiles-button').should('be.disabled')

      cy.selectStationInDropdown(0)

      // Check if the error message showed up
      cy.getByTestId('calculate-percentiles-button').should('not.be.disabled').click() // prettier-ignore
      cy.checkErrorMessage('Error occurred (while getting the calculation result).')
    })

    it('Successful with one station', () => {
      const stationCode = 838
      cy.route('POST', 'api/percentiles/', 'fixture:percentiles/percentile-result.json').as('getPercentiles')

      // Select a station
      cy.selectStationInDropdown(stationCode)

      cy.requestPercentilesAndCheckRequestBody('@getPercentiles', {
        stations: [stationCode],
        year_range: { start: 2010, end: 2019 },
        percentile: 90
      })

      // Mean table shouldn't be shown
      cy.getByTestId('percentile-mean-result-table').should('not.exist')

      // One percentile table should be shown
      cy.getByTestId('percentile-station-result-table').should('have.length', 1)

      // Check values in the table
      cy.contains('Station Name').next().should('contain', `AKOKLI CREEK (${stationCode})`) // prettier-ignore
      cy.getByTestId('percentile-station-result-FFMC').should('contain', NOT_AVAILABLE)
      cy.getByTestId('percentile-station-result-BUI').should('contain', NOT_AVAILABLE)
      cy.getByTestId('percentile-station-result-ISI').should('contain', NOT_AVAILABLE)
    })

    it('Successful with two stations', () => {
      const stationCodes = [322, 1275]
      cy.route('POST', 'api/percentiles/', 'fixture:percentiles/two-percentiles-result.json').as('getPercentiles')

      // Select two weather stations
      cy.selectStationInDropdown(stationCodes[0])
      cy.selectStationInDropdown(stationCodes[1])

      cy.requestPercentilesAndCheckRequestBody('@getPercentiles', {
        stations: stationCodes,
        year_range: { start: 2010, end: 2019 },
        percentile: 90
      })

      // Mean table & two percentile tables should be shown
      cy.getByTestId('percentile-mean-result-table')
      cy.getByTestId('percentile-station-result-table').should('have.length', 2)

      // Results should disappear after clicking the reset button
      cy.getByTestId('reset-percentiles-button').click()
      cy.getByTestId('percentile-mean-result-table').should('not.exist')
      cy.getByTestId('percentile-station-result-table').should('not.exist')
    })
  })
})
