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

    cy.setFBAGrassCurePercentage(grassCure, 1)

    cy.setFBAWindSpeed(windSpeed, 1)

    cy.selectFBAStationInDropdown(stationCode, 1)

    cy.selectFBAFuelTypeInDropdown(fuelType.friendlyName, 1)

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
      cy.selectFBAStationInDropdown(stationCode, 1)

      cy.rowCountShouldBe(1)
      cy.url().should('contain', `s=${stationCode}`)
    })
    it('Can select fuel type successfully', () => {
      cy.intercept('POST', 'api/fba-calc/stations', _ => {
        throw new Error('API request made when only station set')
      })

      visitAndAddRow()

      const fuelType = FuelTypes.get()['c1']
      cy.selectFBAFuelTypeInDropdown(fuelType.friendlyName, 1)

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

      cy.selectFBAStationInDropdown(stationCode, 1)

      cy.selectFBAFuelTypeInDropdown(fuelType.friendlyName, 1)

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
      cy.selectFBAStationInDropdown(stationCode, 1)

      cy.selectFBAFuelTypeInDropdown(FuelTypes.get()['o1a'].friendlyName, 1)
      cy.getByTestId(`fuel-type-dropdown-fba-1`)
        .find('input')
        .clear()
      cy.selectFBAFuelTypeInDropdown(FuelTypes.get()['o1b'].friendlyName, 1)
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

      cy.selectFBAStationInDropdown(322, 1)

      cy.selectFBAFuelTypeInDropdown(FuelTypes.get()['c1'].friendlyName, 1)

      cy.wait('@calculateResults')
    })
  })
  describe('Row management', () => {
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
      cy.selectFBAStationInDropdown(stationCode, 1)

      cy.getByTestId('remove-rows').should('not.have.class', 'Mui-disabled')
    })

    it('Rows can be added and removed', () => {
      cy.intercept('GET', 'api/stations/*', { fixture: 'weather-stations.json' }).as('getStations')

      visitAndAddRow()

      cy.wait('@getStations')

      const stationCode = 322
      cy.selectFBAStationInDropdown(stationCode, 1)

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
      cy.selectFBAStationInDropdown(stationCode, 1)

      cy.rowCountShouldBe(1)
      cy.url().should('contain', `s=${stationCode}`)

      cy.setSelectedRow()

      cy.getByTestId('remove-rows').click()

      cy.rowCountShouldBe(0)
      cy.url().should('not.contain', `s=${stationCode}`)
    })
  })

  describe('Export data to CSV', () => {
    it('Disables the Export button when 0 rows are selected', () => {
      cy.intercept('GET', 'api/stations/*', { fixture: 'weather-stations.json' }).as('getStations')
      visitAndAddRow()
      cy.wait('@getStations')
      cy.selectFBAStationInDropdown(322, 1)
      cy.selectFBAFuelTypeInDropdown('C3', 1)
      cy.getByTestId('export').should('be.visible')
      cy.getByTestId('export').should('be.disabled')
    })

    it('Enables the Export button once 1 or more rows are selected', () => {
      cy.intercept('GET', 'api/stations/*', { fixture: 'weather-stations.json' }).as('getStations')
      visitAndAddRow()
      cy.wait('@getStations')
      cy.selectFBAStationInDropdown(322, 1)
      cy.selectFBAFuelTypeInDropdown('C4', 1)
      cy.getByTestId('select-all').click()
      cy.getByTestId('export').should('be.enabled')
    })

    it.only('Exports selected rows from table to CSV', () => {
      cy.intercept('GET', 'api/stations/*', { fixture: 'weather-stations.json' }).as('getStations')
      visitAndAddRow()
      cy.wait('@getStations')
      cy.setDate('2021-08-30')

      // first station
      const stationCode1 = 322
      const fuelType1 = 'C5'
      cy.selectFBAStationInDropdown(stationCode1, 1)
      cy.selectFBAFuelTypeInDropdown(fuelType1, 1)

      cy.getByTestId('add-row').click()

      cy.intercept('POST', 'api/fba-calc/stations', { fixture: 'fba-calc/322.json' }).as('postFirstStation')

      // second station
      const stationCode2 = 328
      const fuelType2 = 'O1A'
      const grassCure2 = '80'
      cy.selectFBAStationInDropdown(stationCode2, 2)
      cy.selectFBAFuelTypeInDropdown(fuelType2, 2)
      cy.setFBAGrassCurePercentage(grassCure2, 2)

      cy.getByTestId('add-row').click()

      cy.intercept('POST', 'api/fba-calc/stations', { fixture: 'fba-calc/328.json' }).as('postSecondStation')

      cy.wait('@postFirstStation').then((interception) => {
        expect(interception.request.body).to.deep.include({
          date: '2021-08-30'
        })
        const stationInBody = interception.request.body.stations[0]
        expect(stationInBody).to.deep.include({
          id: 1,
          station_code: stationCode1,
          fuel_type: fuelType1
        })
      })

      cy.wait('@postSecondStation').then((interception) => {
        expect(interception.request.body).to.deep.include({
          date: '2021-08-30'
        })
        const stationInBody = interception.request.body.stations[0]
        expect(stationInBody).to.deep.include({
          id: 2,
          station_code: stationCode2,
          fuel_type: fuelType2,
          grass_cure: grassCure2
        })
      })

      cy.getByTestId('select-all').click()
      cy.getByTestId('export').should('be.enabled')
      cy.getByTestId('export').click()

      cy.wait(2000)
      cy.readFile('FireBAT_2021-08-30.csv').should('equal', { fixture: 'fba-calc/export.csv' })
    })
  })
})
