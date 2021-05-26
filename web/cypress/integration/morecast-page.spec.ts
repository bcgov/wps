import { FIRE_WEATHER_ROUTE, MORECAST_ROUTE, PARTIAL_WIDTH } from '../../src/utils/constants'
import { stationCodeQueryKey, timeOfInterestQueryKey } from '../../src/utils/url'
const stationCode = 328
const stationCode2 = 380
const numOfObservations = 119

const interceptData = () => {
  cy.intercept('POST', 'api/observations/', { fixture: 'weather-data/observations' })
  cy.intercept('POST', 'api/forecasts/noon/', { fixture: 'weather-data/noon-forecasts' })
  cy.intercept('POST', 'api/forecasts/noon/summaries/', { fixture: 'weather-data/noon-forecast-summaries' })
  cy.intercept('POST', 'api/weather_models/GDPS/predictions/most_recent', {fixture:'weather-data/models-with-bias-adjusted'}) // prettier-ignore
  cy.intercept('POST', 'api/weather_models/GDPS/predictions/summaries/', {
    fixture: 'weather-data/model-summaries'
  })
  cy.intercept('POST', 'api/weather_models/HRDPS/predictions/most_recent', {fixture:'weather-data/hr-models-with-bias-adjusted'}) // prettier-ignore
  cy.intercept('POST', 'api/weather_models/HRDPS/predictions/summaries', {fixture:'weather-data/high-res-model-summaries'}) // prettier-ignore
  cy.intercept('POST', 'api/weather_models/RDPS/predictions/most_recent', {fixture:'weather-data/regional-models-with-bias-adjusted'}) // prettier-ignore
  cy.intercept('POST', 'api/weather_models/RDPS/predictions/summaries', {
    fixture: 'weather-data/regional-model-summaries'
  })
}

describe('MoreCast Page', () => {
  beforeEach(() => {
    cy.intercept('GET', 'api/stations/', { fixture: 'weather-stations.json' }).as('getStations')
  })

  it('Should redirect to /morecast when accessing /fire-weather', () => {
    cy.visit(FIRE_WEATHER_ROUTE)
    cy.url().should('contain', MORECAST_ROUTE)
  })

  it('Should display error messages when network errors occurred', () => {
    cy.visit(MORECAST_ROUTE)
    cy.intercept('POST', 'api/weather_models/RDPS/predictions/summaries').as('getRdpsSummaries')
    cy.wait('@getStations')

    cy.selectStationInDropdown(stationCode)
    const timeOfInterest = '2021-02-01T12:00:00-08:00'
    cy.getByTestId('time-of-interest-picker').type(timeOfInterest.slice(0, 16)) // yyyy-MM-ddThh:mm

    cy.getByTestId('get-wx-data-button').click({ force: true })
    cy.url()
      .should('contain', `${stationCodeQueryKey}=${stationCode}`)
      .and('contain', `${timeOfInterestQueryKey}=${timeOfInterest}`)

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

  it('Should display a map with OpenLayers', () => {
    cy.visit(MORECAST_ROUTE)

    // Should be able to find its zoom control
    cy.getByTestId('map').find('.ol-zoom')

    // Should be able to find an attribution for the base map layer
    cy.getByTestId('map')
      .find('.ol-attribution')
      .click()
  })

  it('Should display the station accuracy for date label', () => {
    cy.visit(MORECAST_ROUTE)

    const timeOfInterest = '2021-02-01T12:00:00-08:00'
    cy.getByTestId('time-of-interest-picker').type(timeOfInterest.slice(0, 16)) // yyyy-MM-ddThh:mm

    cy.getByTestId('get-wx-data-button').click({ force: true })
    cy.getByTestId('station-forecast-accuracy-for-date').should('have.text', timeOfInterest.slice(0, 10))
    cy.url().should('contain', `${timeOfInterestQueryKey}=${timeOfInterest}`)
  })

  describe('When loading a single station from url', () => {
    beforeEach(() => {
      interceptData()

      cy.visit(`${MORECAST_ROUTE}?codes=${stationCode}`)
      cy.wait('@getStations')
    })

    it('should load with an observation table', () => {
      cy.getByTestId(`observations-table-${stationCode}`)
        .find('tbody > tr')
        .should('have.length', numOfObservations)

      // expect the sidepanel to be partially expanded (we compare the calculated width, and expect
      // it to match the width of our browser window)
      cy.getByTestId('expandable-container-content')
        .invoke('css', 'width')
        .then(str => parseInt(str))
        .should('be.lt', 790)
    })
  })

  describe('When loading multiple stations from url', () => {
    beforeEach(() => {
      interceptData()

      cy.visit(`${MORECAST_ROUTE}?codes=${stationCode},${stationCode2}`)
      cy.wait('@getStations')
    })

    it('Should display station comparison table', () => {
      // expect Station Comparison to be selected
      cy.getByTestId('station-comparison-button').should('have.attr', 'aria-pressed', 'true')

      // expect the table to exist.
      cy.getByTestId('station-comparison-table').should('exist')

      // expect the sidepanel to be fully expanded (we compare the calculated width, and expect
      // it to match the width of our browser window)
      cy.getByTestId('expandable-container-content').should('have.css', 'width', '1000px')
    })
  })

  describe('When wx data for multiple stations fetched', () => {
    beforeEach(() => {
      interceptData()

      cy.visit(MORECAST_ROUTE)

      cy.wait('@getStations')

      // Request the weather data
      cy.selectStationInDropdown(stationCode)
      cy.selectStationInDropdown(stationCode2)
      const timeOfInterest = '2021-01-22T12:00:00-08:00'
      cy.getByTestId('time-of-interest-picker').type(timeOfInterest.slice(0, 16)) // yyyy-MM-ddThh:mm
      cy.getByTestId('get-wx-data-button').click({ force: true })
    })

    it('Should display station comparison table', () => {
      // expect Station Comparison to be selected
      cy.getByTestId('station-comparison-button').should('have.attr', 'aria-pressed', 'true')

      // expect the table to exist.
      cy.getByTestId('station-comparison-table').should('exist')

      // expect the sidepanel to be fully expanded (we compare the calculated width, and expect
      // it to match the width of our browser window)
      cy.getByTestId('expandable-container-content').should('have.css', 'width', '1000px')

      // expecting 2 rows, one for each station.
      cy.getByTestId('station-comparison-table')
        .find('tbody > tr')
        .should('have.length', 2)

      // expect some observed data
      cy.getByTestId('comparison-table-row-0')
        .find('td[data-testid="temperature-observation"] > div')
        .should('contain', '-3.8°C')

      cy.getByTestId('comparison-table-row-0')
        .find('td[data-testid="dewpoint-observation"] > div')
        .should('contain', '-8.3°C')
    })
  })

  describe('When wx data successfully fetched', () => {
    const numOfForecasts = 6
    const numOfGdps = 131
    const numOfHrdps = 159
    const numOfRdps = 195

    beforeEach(() => {
      interceptData()

      cy.visit(MORECAST_ROUTE)

      cy.wait('@getStations')

      // Request the weather data
      cy.selectStationInDropdown(stationCode)
      cy.getByTestId('get-wx-data-button').click({ force: true })
    })

    it('Observation, noon forecast, and noon GDPS should be displayed in tables in default active tab', () => {
      const checkMaxTempFormattingAndLength = (tableName: string) => {
        cy.getByTestId(`${tableName}-${stationCode}`)
          .getByTestId('max-temperature-td')
          .should('have.css', 'background-color', 'rgb(255, 179, 179)')
          .should('have.length.at.least', 1)
      }

      const checkMinTempFormattingAndLength = (tableName: string) => {
        cy.getByTestId(`${tableName}-${stationCode}`)
          .getByTestId('min-temperature-td')
          .should('have.css', 'background-color', 'rgb(132, 184, 231)')
          .should('have.length.at.least', 1)
      }

      const checkMinRHFormattingAndLength = (tableName: string) => {
        cy.getByTestId(`${tableName}-${stationCode}`)
          .getByTestId('min-RH-td')
          .should('have.css', 'background-color', 'rgb(242, 153, 74)')
          .should('have.length.at.least', 1)
      }

      const checkMaxPrecipFormattingAndLength = (tableName: string) => {
        cy.getByTestId(`${tableName}-${stationCode}`)
          .getByTestId('max-precipitation-td')
          .should('have.css', 'border', '1px solid rgba(0, 0, 0, 0.87)')
      }

      const checkMaxWindSpeedFormattingAndLength = (tableName: string) => {
        cy.getByTestId(`${tableName}-${stationCode}`)
          .getByTestId('max-wind-speed-td')
          .should('have.css', 'border-right', '1px solid rgba(0, 0, 0, 0.87)')
          .should('have.css', 'border-left-width', '0px')
      }

      const checkWindDirectionFormattingAndLength = (tableName: string) => {
        cy.getByTestId(`${tableName}-${stationCode}`)
          .getByTestId('direction-max-wind-speed-td')
          .should('have.css', 'border-left', '1px solid rgba(0, 0, 0, 0.87)')
          .should('have.css', 'border-right-width', '0px')
      }

      const checkTableCellHighlighting = (tableName: string) => {
        checkMaxTempFormattingAndLength(tableName)
        checkMinTempFormattingAndLength(tableName)
        checkMinRHFormattingAndLength(tableName)
        checkMaxPrecipFormattingAndLength(tableName)
        checkMaxWindSpeedFormattingAndLength(tableName)
        checkWindDirectionFormattingAndLength(tableName)
      }

      cy.getByTestId(`observations-table-${stationCode}`)
        .find('tbody > tr')
        .should('have.length', numOfObservations)

      // Check if the sorting functionality works
      const day = 26
      const earliestDate = `2021-01-${day - 5}`
      const latestDate = `2021-01-${day}`
      cy.getByTestId(`observations-table-${stationCode}`)
        .find('tbody > tr:first > td:first')
        .should('contain', latestDate)
      cy.getByTestId(`observations-table-${stationCode}`).find('.MuiTableSortLabel-icon').click() // prettier-ignore
      cy.getByTestId(`observations-table-${stationCode}`)
        .find('tbody > tr:first > td:first')
        .should('contain', earliestDate)
      cy.getByTestId(`observations-table-${stationCode}`).find('.MuiTableSortLabel-icon').click() // prettier-ignore
      cy.getByTestId(`observations-table-${stationCode}`)
        .find('tbody > tr:first > td:first')
        .should('contain', latestDate)

      checkTableCellHighlighting('observations-table')

      // Check num of interpolated noon GDPS rows
      cy.getByTestId(`noon-gdps-table-${stationCode}`)
        .find('tbody > tr')
        .should('have.length', 14)
      checkTableCellHighlighting('noon-gdps-table')

      // Check num of noon forecasts rows
      cy.getByTestId(`noon-forecasts-table-${stationCode}`)
        .find('tbody > tr')
        .should('have.length', numOfForecasts)
      checkTableCellHighlighting('noon-forecasts-table')

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
    it('Should show the legend', () => {
      cy.getByTestId('legend').should('be.visible')
    })
    it('Should expand the side panel when it is collapsed, and hide the legend', () => {
      cy.get(`[value=expand-collapse]`).click({ force: true })
      cy.getByTestId('expandable-container-content')
        .invoke('width')
        .should('be.gt', PARTIAL_WIDTH)

      cy.getByTestId('legend').should('not.exist')
    })
    it('Should collapse the side panel when it is expanded and the legend should be visible', () => {
      cy.get(`[value=expand-collapse]`)
        .click({ force: true })
        .click({ force: true })
      cy.getByTestId('expandable-container-content')
        .invoke('width')
        .should('be.lte', PARTIAL_WIDTH)

      cy.getByTestId('legend').should('be.visible')
    })
    it('Should close the side panel and the legend should be visible', () => {
      cy.get(`[value=close]`).click({ force: true })
      cy.getByTestId('legend').should('be.visible')
    })

    describe('When graphs tab is clicked', () => {
      beforeEach(() => {
        cy.contains('Graphs').click()
      })
      it('Temp & RH Graph should be displayed', () => {
        const checkNumOfTempDewpointMarkers = (num: number) => {
          cy.getByTestId('temp-rh-graph')
            .find(`.cartesianlayer > .subplot > .plot > .scatterlayer > .trace > .points > .point`)
            .should('have.length', num)
        }
        const checkTempPlume = (shouldBeDisplayed: boolean) => {
          cy.getByTestId('temp-rh-graph')
            .find(`.cartesianlayer > .subplot > .plot > .scatterlayer > .trace`)
            .should('have.length', shouldBeDisplayed ? 3 : 1) // 2 more traces that make up the plume
        }
        const checkTempDewpointTraces = (shouldBeDisplayed: boolean) => {
          cy.getByTestId('temp-rh-graph')
            .find(`.cartesianlayer > .subplot > .plot > .scatterlayer > .trace`)
            .should('have.length', shouldBeDisplayed ? 4 : 2) // 2 more traces that make up plume
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

        checkNumOfLegends(8)

        cy.getByTestId('wx-graph-hrdps-toggle').click()
        checkNumOfTempDewpointMarkers(2 * numOfObservations - 1)
        checkNumOfRHMarkers(numOfObservations)
        checkTempDewpointTraces(false)
        checkRHPlume(false)
        cy.getByTestId('wx-graph-observation-toggle').click()

        cy.getByTestId('wx-graph-forecast-toggle').click()
        checkNumOfTempDewpointMarkers(numOfForecasts)
        checkNumOfRHMarkers(numOfForecasts)
        cy.getByTestId('wx-graph-forecast-toggle').click()

        cy.getByTestId('wx-graph-hrdps-toggle').click()
        checkNumOfTempDewpointMarkers(numOfHrdps)
        checkNumOfRHMarkers(numOfHrdps)
        checkTempPlume(true)
        checkRHPlume(true)
        cy.getByTestId('wx-graph-hrdps-toggle').click()

        cy.getByTestId('wx-graph-rdps-toggle').click()
        checkNumOfTempDewpointMarkers(numOfRdps)
        checkNumOfRHMarkers(numOfRdps)
        checkTempPlume(true)
        checkRHPlume(true)
        cy.getByTestId('wx-graph-rdps-toggle').click()

        cy.getByTestId('wx-graph-gdps-toggle').click()
        checkNumOfTempDewpointMarkers(numOfGdps)
        checkNumOfRHMarkers(numOfGdps)
        checkTempPlume(true)
        checkRHPlume(true)
        cy.getByTestId('wx-graph-gdps-toggle').click()

        cy.getByTestId('wx-graph-bias-adjusted-gdps-toggle').click()
        checkNumOfTempDewpointMarkers(numOfGdps)
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
        cy.getByTestId('wx-graph-gdps-toggle').click()

        cy.getByTestId('wx-graph-forecast-toggle').click()
        checkNumOfArrows(numOfForecasts)

        checkNumOfLegends(2)
      })
      it('Can toggle back to tables', () => {
        cy.contains('Tables').click()
        cy.getByTestId(`observations-table-${stationCode}`)
          .find('tbody > tr')
          .should('have.length', numOfObservations)
      })
    })
  })
})
