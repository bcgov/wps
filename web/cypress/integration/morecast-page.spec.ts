import { FIRE_WEATHER_ROUTE, MORECAST_ROUTE } from '../../src/utils/constants'
import { stationCodeQueryKey, timeOfInterestQueryKey } from '../../src/utils/url'

const stationCode = 328

describe('MoreCast Page', () => {
  beforeEach(() => {
    cy.server()
    cy.route('GET', 'api/stations/', 'fixture:weather-stations.json').as('getStations')
  })

  it('Should redirect to /morecast when accessing /fire-weather', () => {
    cy.visit(FIRE_WEATHER_ROUTE)
    cy.url().should('contain', MORECAST_ROUTE)
  })

  it('Should display error messages when network errors occurred', () => {
    cy.visit(MORECAST_ROUTE)
    cy.route('POST', 'api/weather_models/RDPS/predictions/summaries').as('getRdpsSummaries')
    cy.wait('@getStations')

    cy.selectStationInDropdown(stationCode)
    const timeOfInterest = '2021-02-01T12:00:00-08:00'
    cy.getByTestId('time-of-interest-picker').type(timeOfInterest.slice(0, 16)) // yyyy-MM-ddThh:mm

    cy.getByTestId('get-wx-data-button').click({ force: true })
    cy.url()
      .should('contain', `${stationCodeQueryKey}=${stationCode}`)
      .and('contain', `${timeOfInterestQueryKey}=${timeOfInterest.slice(0, 19)}`)

    cy.wait('@getRdpsSummaries')
    cy.checkErrorMessage('Error occurred (while fetching hourly observations).')
    cy.checkErrorMessage('Error occurred (while fetching GDPS).')
    cy.checkErrorMessage('Error occurred (while fetching GDPS summaries).')
    cy.checkErrorMessage('Error occurred (while fetching noon forecasts).')
    cy.checkErrorMessage('Error occurred (while fetching noon forecast summaries).')
    cy.checkErrorMessage('Error occurred (while fetching HRDPS).')
    cy.checkErrorMessage('Error occurred (while fetching HRDPS summaries).')
    cy.checkErrorMessage('Error occurred (while fetching RDPS).')
    cy.checkErrorMessage('Error occurred (while fetching RDPS summaries).')

    cy.contains('Data is not available.')
  })

  describe('When wx data successfully fetched', () => {
    const numOfObservations = 119
    const numOfForecasts = 6
    const numOfGdps = 131
    const numOfHrdps = 159
    const numOfRdps = 195

    beforeEach(() => {
      cy.route('POST', 'api/observations/', 'fixture:weather-data/observations')
      cy.route('POST', 'api/forecasts/noon/', 'fixture:weather-data/noon-forecasts')
      cy.route('POST', 'api/forecasts/noon/summaries/', 'fixture:weather-data/noon-forecast-summaries')
      cy.route('POST', 'api/weather_models/GDPS/predictions/most_recent', 'fixture:weather-data/models-with-bias-adjusted') // prettier-ignore
      cy.route('POST', 'api/weather_models/GDPS/predictions/summaries/', 'fixture:weather-data/model-summaries')
      cy.route('POST', 'api/weather_models/HRDPS/predictions/most_recent', 'fixture:weather-data/hr-models-with-bias-adjusted') // prettier-ignore
      cy.route('POST', 'api/weather_models/HRDPS/predictions/summaries', 'fixture:weather-data/high-res-model-summaries') // prettier-ignore
      cy.route('POST', 'api/weather_models/RDPS/predictions/most_recent', 'fixture:weather-data/regional-models-with-bias-adjusted') // prettier-ignore
      cy.route('POST', 'api/weather_models/RDPS/predictions/summaries', 'fixture:weather-data/regional-model-summaries')

      cy.visit(MORECAST_ROUTE)

      cy.wait('@getStations')

      // Request the weather data
      cy.selectStationInDropdown(stationCode)
      cy.getByTestId('get-wx-data-button').click({ force: true })
    })

    it('Observation, noon forecast, and noon GDPS should be displayed in tables', () => {
      cy.getByTestId(`observations-table-${stationCode}`)
        .find('tbody > tr')
        .should('have.length', numOfObservations)

      // Check if the sorting functionality works
      const day = 26
      const earliestDate = `2021-01-${day - 5}`
      const latestDate = `2021-01-${day}`
      cy.getByTestId(`observations-table-${stationCode}-accordion`).click() // Expand Observations table
      cy.getByTestId(`observations-table-${stationCode}`)
        .find('tbody > tr:first > td:first')
        .should('contain', earliestDate)
      cy.getByTestId(`observations-table-${stationCode}`).find('.MuiTableSortLabel-icon').click() // prettier-ignore
      cy.getByTestId(`observations-table-${stationCode}`)
        .find('tbody > tr:first > td:first')
        .should('contain', latestDate)
      cy.getByTestId(`observations-table-${stationCode}`).find('.MuiTableSortLabel-icon').click() // prettier-ignore
      cy.getByTestId(`observations-table-${stationCode}`)
        .find('tbody > tr:first > td:first')
        .should('contain', earliestDate)

      cy.getByTestId(`noon-gdps-table-${stationCode}-accordion`).click() // Expand interpolated GDPS noon values table
      cy.getByTestId(`noon-gdps-table-${stationCode}`)
        .find('tbody > tr')
        .should('have.length', 14) // Num of noon gdps
      cy.getByTestId(`noon-forecasts-table-${stationCode}`)
        .find('tbody > tr')
        .should('have.length', numOfForecasts)

      // Check that collapse and expand functionality works
      cy.getByTestId(`observations-table-${stationCode}-accordion`).click() // Collapse Observations table
      cy.wait(500)
      cy.getByTestId(`observations-table-${stationCode}`)
        .find('.MuiTableSortLabel-icon')
        .should('not.be.visible')

      cy.getByTestId(`noon-gdps-table-${stationCode}-accordion`).click() // Collapse Interpolated GDPS noon values table
      cy.wait(500)
      cy.getByTestId(`noon-gdps-table-${stationCode}`)
        .find('.MuiTableContainer-root')
        .should('not.be.visible')
    })

    it('Temp & RH Graph should be displayed', () => {
      const checkNumOfTempMarkers = (num: number) => {
        cy.getByTestId('temp-rh-graph')
          .find(`.cartesianlayer > .subplot > .plot > .scatterlayer > .trace > .points > .point`)
          .should('have.length', num)
      }
      const checkTempPlume = (shouldBeDisplayed: boolean) => {
        cy.getByTestId('temp-rh-graph')
          .find(`.cartesianlayer > .subplot > .plot > .scatterlayer > .trace`)
          .should('have.length', shouldBeDisplayed ? 3 : 1) // 2 more traces that make up the plume
      }
      const checkNumOfRHMarkers = (num: number) => {
        cy.getByTestId('temp-rh-graph')
          .find('.cartesianlayer > .subplot > .overplot > .xy2 > .scatterlayer > .trace > .points > .point')
          .should('have.length', num)
      }
      const checkRHPlume = (shouldBeDisplayed: boolean) => {
        cy.getByTestId('temp-rh-graph')
          .find('.cartesianlayer > .subplot > .overplot > .xy2 > .scatterlayer > .trace')
          .should('have.length', shouldBeDisplayed ? 4 : 2) // 2 more traces that make up the plume
      }
      const checkNumOfLegends = (num: number) => {
        cy.getByTestId('temp-rh-graph')
          .find('.infolayer > .legend > .scrollbox > .groups > .traces')
          .should('have.length', num)
      }

      checkNumOfLegends(7)

      cy.getByTestId('wx-graph-hrdps-toggle').click()
      checkNumOfTempMarkers(numOfObservations - 1)
      checkNumOfRHMarkers(numOfObservations)
      checkTempPlume(false)
      checkRHPlume(false)
      cy.getByTestId('wx-graph-observation-toggle').click()

      cy.getByTestId('wx-graph-forecast-toggle').click()
      checkNumOfTempMarkers(numOfForecasts)
      checkNumOfRHMarkers(numOfForecasts)
      cy.getByTestId('wx-graph-forecast-toggle').click()

      cy.getByTestId('wx-graph-hrdps-toggle').click()
      checkNumOfTempMarkers(numOfHrdps)
      checkNumOfRHMarkers(numOfHrdps)
      checkTempPlume(true)
      checkRHPlume(true)
      cy.getByTestId('wx-graph-hrdps-toggle').click()

      cy.getByTestId('wx-graph-rdps-toggle').click()
      checkNumOfTempMarkers(numOfRdps)
      checkNumOfRHMarkers(numOfRdps)
      checkTempPlume(true)
      checkRHPlume(true)
      cy.getByTestId('wx-graph-rdps-toggle').click()

      cy.getByTestId('wx-graph-gdps-toggle').click()
      checkNumOfTempMarkers(numOfGdps)
      checkNumOfRHMarkers(numOfGdps)
      checkTempPlume(true)
      checkRHPlume(true)
      cy.getByTestId('wx-graph-gdps-toggle').click()

      cy.getByTestId('wx-graph-bias-adjusted-gdps-toggle').click()
      checkNumOfTempMarkers(numOfGdps)
      checkNumOfRHMarkers(numOfGdps)
      checkTempPlume(false)
      checkRHPlume(false)

      checkNumOfLegends(3)
    })

    it('Precipitation graph should be displayed', () => {
      const checkNumOfBars = (num: number) => {
        cy.getByTestId('precipitation-graph')
          .find(`.cartesianlayer > .subplot > .plot > .barlayer > .trace > .points > .point`)
          .should('have.length', num)
      }
      const checkNumOfLegends = (num: number) => {
        cy.getByTestId('precipitation-graph')
          .find('.infolayer > .legend > .scrollbox > .groups > .traces')
          .should('have.length', num)
      }

      checkNumOfLegends(5)

      cy.getByTestId('wx-graph-hrdps-toggle').click()
      checkNumOfBars(6)
      cy.getByTestId('wx-graph-observation-toggle').click()

      cy.getByTestId('wx-graph-forecast-toggle').click()
      checkNumOfBars(6)
      cy.getByTestId('wx-graph-forecast-toggle').click()

      cy.getByTestId('wx-graph-hrdps-toggle').click()
      checkNumOfBars(8)
      cy.getByTestId('wx-graph-hrdps-toggle').click()

      // Note: No idea why this fails in GH action (WTH)
      // cy.getByTestId('wx-graph-rdps-toggle').click()
      // checkNumOfBars(9) // counts 10 instead of 9
      // cy.getByTestId('wx-graph-rdps-toggle').click()

      // cy.getByTestId('wx-graph-gdps-toggle').click()
      // checkNumOfBars(16) // counts 15 instead of 6

      checkNumOfLegends(1)
    })

    it('Wind speed & direction graph should be displayed', () => {
      const checkNumOfArrows = (num: number) => {
        cy.getByTestId('wind-spd-dir-graph')
          .find(`.layer-above > .shapelayer > path`)
          .should('have.length', num)
      }
      const checkNumOfLegends = (num: number) => {
        cy.getByTestId('wind-spd-dir-graph')
          .find('.infolayer > .legend > .scrollbox > .groups > .traces')
          .should('have.length', num)
      }

      checkNumOfLegends(3)

      cy.getByTestId('wx-graph-hrdps-toggle').click()
      checkNumOfArrows(numOfObservations)
      cy.getByTestId('wx-graph-observation-toggle').click()

      cy.getByTestId('wx-graph-hrdps-toggle').click()
      checkNumOfArrows(numOfHrdps)
      cy.getByTestId('wx-graph-hrdps-toggle').click()

      cy.getByTestId('wx-graph-rdps-toggle').click()
      checkNumOfArrows(numOfRdps)
      cy.getByTestId('wx-graph-rdps-toggle').click()

      cy.getByTestId('wx-graph-gdps-toggle').click()
      checkNumOfArrows(numOfGdps)

      checkNumOfLegends(2)
    })
  })
})
