import { FIRE_BEHAVIOR_CALC_ROUTE } from '../../src/utils/constants'
import { FuelTypes } from '../../src/features/fbaCalculator/fuelTypes'
import { DateTime } from 'luxon'

describe('FireBAT Calculator Page', () => {
  const visitAndAddRow = () => {
    cy.visit(FIRE_BEHAVIOR_CALC_ROUTE)

    cy.getByTestId('add-row').click()
  }
  it('Sets all the input fields for calculating results on the backend', () => {
    cy.intercept('GET', 'api/stations/*', { fixture: 'weather-stations.json' }).as('getStations')
    const stationCode = 322
    const fuelType = FuelTypes.get()['c1']
    const grassCure = '1'
    const windSpeed = '2'

    cy.intercept('POST', 'api/fba-calc/stations', req => {
      expect(req.body.stations[0]).to.deep.include({
        station_code: stationCode,
        fuel_type: fuelType.name,
        percentage_conifer: fuelType.percentage_conifer,
        crown_base_height: fuelType.crown_base_height,
        grass_cure: parseInt(grassCure),
        wind_speed: parseFloat(windSpeed)
      })
    }).as('calculateResults')

    visitAndAddRow()

    cy.wait('@getStations')

    cy.setFBAGrassCurePercentage(grassCure)

    cy.setFBAWindSpeed(windSpeed)

    cy.selectFBAStationInDropdown(stationCode)

    cy.selectFBAFuelTypeInDropdown(fuelType.friendlyName)

    cy.wait('@calculateResults')

    cy.rowCountShouldBe(1)
    cy.url().should('contain', `s=${stationCode}&f=${fuelType.name.toLowerCase()}&c=${grassCure}&w=${windSpeed}`)
  })
  describe('Dropdowns', () => {
    it('Can select station if successfully received stations', () => {
      cy.intercept('GET', 'api/stations/*', { fixture: 'weather-stations.json' }).as('getStations')
      cy.intercept('POST', 'api/fba-calc/stations', _ => {
        throw new Error('API request made when only station set')
      })

      visitAndAddRow()

      cy.wait('@getStations')

      const stationCode = 322
      cy.selectFBAStationInDropdown(stationCode)

      cy.rowCountShouldBe(1)
      cy.url().should('contain', `s=${stationCode}`)
    })
    it('Can select fuel type successfully', () => {
      cy.intercept('POST', 'api/fba-calc/stations', _ => {
        throw new Error('API request made when only station set')
      })

      visitAndAddRow()

      const fuelType = FuelTypes.get()['c1']
      cy.selectFBAFuelTypeInDropdown(fuelType.friendlyName)

      cy.rowCountShouldBe(1)
      cy.url().should('contain', `f=${fuelType.name.toLowerCase()}`)
    })

    it('Calls backend when station and non-grass fuel type are set', () => {
      cy.intercept('GET', 'api/stations/*', { fixture: 'weather-stations.json' }).as('getStations')
      const stationCode = 322
      const fuelType = FuelTypes.get()['c1']

      cy.intercept('POST', 'api/fba-calc/stations', req => {
        expect(req.body.stations[0]).to.deep.include({
          station_code: stationCode,
          fuel_type: fuelType.name,
          percentage_conifer: fuelType.percentage_conifer,
          crown_base_height: fuelType.crown_base_height
        })
      }).as('calculateResults')

      visitAndAddRow()

      cy.wait('@getStations')

      cy.selectFBAStationInDropdown(stationCode)

      cy.selectFBAFuelTypeInDropdown(fuelType.friendlyName)

      cy.rowCountShouldBe(1)
      cy.url().should('contain', `s=${stationCode}&f=${fuelType.name.toLowerCase()}`)

      cy.wait('@calculateResults')
    })
    it('Does not call backend when station and grass fuel type are set without grass cure percentage', () => {
      cy.intercept('GET', 'api/stations/*', { fixture: 'weather-stations.json' }).as('getStations')
      cy.intercept('POST', 'api/fba-calc/stations', _ => {
        throw new Error('API request made without grass cure percentage set')
      })

      visitAndAddRow()

      cy.wait('@getStations')

      const stationCode = 322
      cy.selectFBAStationInDropdown(stationCode)

      cy.selectFBAFuelTypeInDropdown(FuelTypes.get()['o1a'].friendlyName)
      cy.getByTestId(`fuel-type-dropdown-fba`)
        .find('input')
        .clear()
      cy.selectFBAFuelTypeInDropdown(FuelTypes.get()['o1b'].friendlyName)
    })
  })

  describe('Date picker', () => {
    it('Sets the date correctly', () => {
      cy.intercept('GET', 'api/stations/*', { fixture: 'weather-stations.json' }).as('getStations')

      const yesterday = DateTime.now()
        .minus({ days: 1 })
        .toISODate()
        .slice(0, 10) // 'YYYY-MM-DD'

      cy.intercept('POST', 'api/fba-calc/stations', req => {
        expect(req.body).to.deep.include({
          date: yesterday
        })
      }).as('calculateResults')

      visitAndAddRow()

      cy.wait('@getStations')

      cy.setDate(yesterday)

      cy.selectFBAStationInDropdown(322)

      cy.selectFBAFuelTypeInDropdown(FuelTypes.get()['c1'].friendlyName)

      cy.wait('@calculateResults')
    })
  })
  xdescribe('Row management', () => {
    it('Disables remove row(s) button when table is empty', () => {
      cy.intercept('GET', 'api/stations/*', { fixture: 'weather-stations.json' }).as('getStations')
      cy.visit(FIRE_BEHAVIOR_CALC_ROUTE)

      cy.getByTestId('remove-rows').should('have.class', 'Mui-disabled')
    })

    it('Enables remove row(s) button when table is not empty', () => {
      cy.intercept('GET', 'api/stations/*', { fixture: 'weather-stations.json' }).as('getStations')

      visitAndAddRow()

      cy.wait('@getStations')

      const stationCode = 322
      cy.selectFBAStationInDropdown(stationCode)

      cy.getByTestId('remove-rows').should('not.have.class', 'Mui-disabled')
    })

    it('Rows can be added and removed', () => {
      cy.intercept('GET', 'api/stations/*', { fixture: 'weather-stations.json' }).as('getStations')

      visitAndAddRow()

      cy.wait('@getStations')

      const stationCode = 322
      cy.selectFBAStationInDropdown(stationCode)

      cy.rowCountShouldBe(1)
      cy.url().should('contain', `s=${stationCode}`)

      cy.getByTestId('select-all').click()

      cy.getByTestId('remove-rows').click()

      cy.rowCountShouldBe(0)
      cy.url().should('not.contain', `s=${stationCode}`)
    })
    it('Specific rows can be removed', () => {
      cy.intercept('GET', 'api/stations/*', { fixture: 'weather-stations.json' }).as('getStations')

      visitAndAddRow()

      cy.wait('@getStations')

      const stationCode = 322
      cy.selectFBAStationInDropdown(stationCode)

      cy.rowCountShouldBe(1)
      cy.url().should('contain', `s=${stationCode}`)

      cy.setSelectedRow()

      cy.getByTestId('remove-rows').click()

      cy.rowCountShouldBe(0)
      cy.url().should('not.contain', `s=${stationCode}`)
    })
  })
})
