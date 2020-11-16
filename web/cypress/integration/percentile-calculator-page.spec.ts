import { NOT_AVAILABLE } from '../../src/utils/strings'

describe('Percentile Calculator Page', () => {
  beforeEach(() => {
    cy.server()
  })

  describe('Weather station dropdown', () => {
    it('renders error message when fetching stations failed', () => {
      cy.visit('/percentile-calculator/')
      cy.getByTestId('disclaimer-accept-button').click()
      cy.checkErrorMessage('Error occurred (while fetching weather stations).')
    })

    it('can select & deselect stations if successfully received stations', () => {
      cy.route('GET', 'api/stations/', 'fixture:weather-stations.json').as('getStations')
      cy.visit('/percentile-calculator/')
      cy.getByTestId('disclaimer-accept-button').click()
      cy.wait('@getStations')

      // Select the first station in the dropdown list
      cy.selectStationByCode(1275)

      // Deselect the selected station
      cy.get('.MuiChip-deleteIcon').click()

      // Select multiple stations in the dropdown and check if only 3 stations were selected
      cy.selectStationByCode(322)
      cy.selectStationByCode(209)
      cy.selectStationByCode(1275)
      cy.selectStationByCode(838)
      cy.get('.MuiChip-deletable').should('have.length', 3)
    })
  })

  describe('For analytics', () => {
    it('Some DOM elements should exist with IDs', () => {
      cy.visit('/percentile-calculator/')
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
      cy.route('POST', 'api/percentiles/').as('getPercentiles')
      cy.visit('/percentile-calculator/')
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
      cy.selectStationByCode(stationCode)

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
      cy.visit('/percentile-calculator/', {
        onBeforeLoad: (win: any) => {
          win._mtm = { push: () => {} } // mock Matomo object
        }
      })
      cy.getByTestId('disclaimer-accept-button').click()
    })

    it('failed due to network error', () => {
      // Calculate button should be disabled if no stations selected
      cy.getByTestId('calculate-percentiles-button').should('be.disabled')

      cy.selectStationByCode(0)

      // Check if the error message showed up
      cy.getByTestId('calculate-percentiles-button').should('not.be.disabled').click() // prettier-ignore
      cy.checkErrorMessage('Error occurred (while getting the calculation result).')
    })

    it('successful with one station', () => {
      const stationCode = 838
      cy.route('POST', 'api/percentiles/', 'fixture:percentiles/percentile-result.json').as('getPercentiles')

      // Select a station
      cy.selectStationByCode(stationCode)

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

    it('successful with two stations', () => {
      const stationCodes = [322, 1275]
      cy.route('POST', 'api/percentiles/', 'fixture:percentiles/two-percentiles-result.json').as('getPercentiles')

      // Select two weather stations
      cy.selectStationByCode(stationCodes[0])
      cy.selectStationByCode(stationCodes[1])

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
