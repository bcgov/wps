import { MORECAST_ROUTE } from '../../src/utils/constants'
import { stationCodeQueryKey } from '../../src/utils/url'

describe('MoreCast Page', () => {
  const stationCode = 328

  beforeEach(() => {
    cy.server()
    cy.route('GET', 'api/stations/', 'fixture:weather-stations.json').as('getStations')
    cy.visit(MORECAST_ROUTE)
  })

  it('When network errors occurred', () => {
    cy.wait('@getStations')

    cy.selectStationInDropdown(stationCode)
    cy.getByTestId('get-wx-data-button').click({ force: true })
    cy.url().should('contain', `${stationCodeQueryKey}=${stationCode}`)

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
    beforeEach(() => {
      cy.route('POST', 'api/hourlies/', 'fixture:weather-data/observations')
      cy.route('POST', 'api/noon_forecasts/', 'fixture:weather-data/noon-forecasts')
      cy.route('POST', 'api/noon_forecasts/summaries/', 'fixture:weather-data/noon-forecast-summaries')
      cy.route('POST', 'api/models/GDPS/predictions/most_recent', 'fixture:weather-data/models-with-bias-adjusted') // prettier-ignore
      cy.route('POST', 'api/models/GDPS/predictions/summaries/', 'fixture:weather-data/model-summaries')
      cy.route('POST', 'api/models/HRDPS/predictions/most_recent', 'fixture:weather-data/hr-models-with-bias-adjusted') // prettier-ignore
      cy.route('POST', 'api/models/HRDPS/predictions/summaries', 'fixture:weather-data/high-res-model-summaries') // prettier-ignore
      cy.route('POST', 'api/models/RDPS/predictions/most_recent', 'fixture:weather-data/regional-models-with-bias-adjusted') // prettier-ignore
      cy.route('POST', 'api/models/RDPS/predictions/summaries', 'fixture:weather-data/regional-model-summaries')
      cy.wait('@getStations')

      // Request the weather data
      cy.selectStationInDropdown(stationCode)
      cy.getByTestId('get-wx-data-button').click({ force: true })
    })

    it('Temp & RH graph displays svg graphics with toggles', () => {
      // Check if svg elements are displayed in the graph
      cy.getByTestId('hourly-observed-temp-symbol')
      cy.getByTestId('hourly-observed-temp-path')
      cy.getByTestId('hourly-observed-rh-symbol')
      cy.getByTestId('hourly-observed-rh-path')
      cy.getByTestId('wx-graph-observation-toggle').click()
      cy.getByTestId('hourly-observed-temp-symbol').should('not.exist')
      cy.getByTestId('hourly-observed-rh-symbol').should('not.exist')

      // Test the toggle buttons
      cy.getByTestId('wx-graph-global-model-toggle').click()
      cy.getByTestId('model-summary-temp-area')
      cy.getByTestId('model-temp-symbol').should('have.length', 130)
      cy.getByTestId('wx-graph-global-model-toggle').click()
      cy.getByTestId('model-summary-temp-area').should('not.exist')
      cy.getByTestId('model-temp-symbol').should('not.exist')

      cy.getByTestId('wx-graph-forecast-toggle').click()
      cy.getByTestId('forecast-temp-dot').should('have.length', 6)
      cy.getByTestId('forecast-summary-temp-line')
      cy.getByTestId('wx-graph-forecast-toggle').click()
      cy.getByTestId('forecast-temp-dot').should('not.exist')
      cy.getByTestId('forecast-summary-temp-line').should('not.exist')

      cy.getByTestId('wx-graph-bias-toggle').click()
      cy.getByTestId('bias-adjusted-model-temp-symbol').should('have.length', 130)
      cy.getByTestId('bias-adjusted-model-temp-path')
      cy.getByTestId('wx-graph-bias-toggle').click()
      cy.getByTestId('bias-adjusted-model-temp-symbol').should('not.exist')

      cy.getByTestId('wx-graph-high-res-model-toggle').click()
      cy.getByTestId('high-res-model-summary-temp-area')
      cy.getByTestId('high-res-model-temp-symbol').should('have.length', 103)
      cy.getByTestId('high-res-model-temp-path')
      cy.getByTestId('wx-graph-high-res-model-toggle').click()
      cy.getByTestId('high-res-model-summary-temp-area').should('not.exist')
      cy.getByTestId('high-res-model-temp-symbol').should('not.exist')

      cy.getByTestId('wx-graph-regional-model-toggle').click()
      cy.getByTestId('regional-model-summary-temp-area')
      cy.getByTestId('regional-model-temp-symbol').should('have.length', 103)
      cy.getByTestId('regional-model-temp-path')
      cy.getByTestId('wx-graph-regional-model-toggle').click()
      cy.getByTestId('regional-model-summary-rh-area').should('not.exist')
      cy.getByTestId('regional-model-rh-symbol').should('not.exist')
    })

    it('Temp & RH graph displays a tooltip & sidebar ', () => {
      // Hover over the first dot and check if the tooltip shows up with the correct text
      cy.getByTestId('hourly-observed-rh-symbol')
        .first()
        .trigger('mousemove', { force: true, x: 3, y: 1 })
      cy.getByTestId('temp-rh-tooltip-text').contains('tspan', /(PDT, UTC-7)/)
      cy.getByTestId('temp-rh-tooltip-text')
        .should('contain', 'Observed Temp: - (°C)')
        .and('contain', 'Observed RH: 61 (%)')

      cy.window().then(win => {
        // Move sidebar all the way to the right
        cy.get('.sidebar')
          .find('.selection')
          .trigger('mousedown', { view: win })
          .trigger('mousemove', {
            clientX: 800,
            clientY: 300,
            force: true
          })
          .trigger('mouseup', {
            force: true,
            view: win
          })

        // Resize it to fit the whole domain
        cy.get('.sidebar')
          .find('.handle--w')
          .trigger('mousedown', { view: win })
          .trigger('mousemove', {
            clientX: 0,
            force: true
          })
          .trigger('mouseup', {
            force: true,
            view: win
          })
      })
    })

    it('Precip graph displays svg graphics and a tooltip', () => {
      // Check if svg elements are displayed (or not) in the graph
      cy.getByTestId('observed-precip-line').should('not.have.class', 'precipLine--hidden')
      cy.getByTestId('forecast-precip-line').should('have.class', 'precipLine--hidden')
      cy.getByTestId('gdps-precip-line').should('have.class', 'precipLine--hidden')
      cy.getByTestId('rdps-precip-line').should('have.class', 'precipLine--hidden')
      cy.getByTestId('hrdps-precip-line').should('have.class', 'precipLine--hidden')
      cy.getByTestId('wx-graph-observation-toggle').click()
      cy.getByTestId('wx-graph-forecast-toggle').click()
      cy.getByTestId('observed-precip-line').should('have.class', 'precipLine--hidden')
      cy.getByTestId('forecast-precip-line').should('not.have.class', 'precipLine--hidden')
      cy.getByTestId('wx-graph-regional-model-toggle').click()
      cy.getByTestId('rdps-precip-line').should('not.have.class', 'precipLine--hidden')
      cy.getByTestId('gdps-precip-line').should('have.class', 'precipLine--hidden')
      cy.getByTestId('wx-graph-high-res-model-toggle').click()
      cy.getByTestId('wx-graph-global-model-toggle').click()
      cy.getByTestId('hrdps-precip-line').should('not.have.class', 'precipLine--hidden')
      cy.getByTestId('gdps-precip-line').should('not.have.class', 'precipLine--hidden')
      cy.getByTestId('wx-graph-observation-toggle').click()

      // Hover over the first date and check if the tooltip shows up with a correct text
      cy.getByTestId('observed-precip-line')
        .first()
        .trigger('mousemove', { force: true, x: 3, y: 1 })
      cy.getByTestId('precip-tooltip-text').contains('tspan', /(PDT, UTC-7)/)
      cy.getByTestId('precip-tooltip-text')
        .should('contain', 'Observed Precip: 0.4 (mm/cm)')
        .and('contain', 'Forecast Precip: 1 (mm/cm)')
    })
  })
})
