import { FIRE_BEHAVIOR_CALC_ROUTE } from '../../src/utils/constants'
import { FuelTypes } from '../../src/features/fbaCalculator/fuelTypes'
import { DateTime } from 'luxon'

describe('FireBAT Calculator Page', () => {
  describe('Dropdowns', () => {
    it('Can select station if successfully received stations', () => {
      cy.intercept('GET', 'api/stations/*', { fixture: 'weather-stations.json' }).as('getStations')
      cy.intercept('POST', 'api/fba-calc/stations', _ => {
        throw new Error('API request made when only station set')
      })
      cy.visit(FIRE_BEHAVIOR_CALC_ROUTE)

      cy.getByTestId('add-row').click()

      cy.wait('@getStations')

      const stationCode = 322
      cy.selectFBAStationInDropdown(0, stationCode)

      cy.url().should('contain', `s=${stationCode}`)
    })
    it('Can select fuel type successfully', () => {
      cy.intercept('POST', 'api/fba-calc/stations', _ => {
        throw new Error('API request made when only station set')
      })
      cy.visit(FIRE_BEHAVIOR_CALC_ROUTE)

      cy.getByTestId('add-row').click()

      const fuelType = FuelTypes.get()['c1']
      cy.selectFBAFuelTypeInDropdown(0, fuelType.friendlyName)

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

      cy.visit(FIRE_BEHAVIOR_CALC_ROUTE)

      cy.getByTestId('add-row').click()

      cy.wait('@getStations')

      cy.selectFBAStationInDropdown(0, stationCode)

      cy.selectFBAFuelTypeInDropdown(0, fuelType.friendlyName)

      cy.url().should('contain', `s=${stationCode}&f=${fuelType.name.toLowerCase()}`)

      cy.wait('@calculateResults')
    })
    it('Does not call backend when station and grass fuel type are set without grass cure percentage', () => {
      cy.intercept('GET', 'api/stations/*', { fixture: 'weather-stations.json' }).as('getStations')
      cy.intercept('POST', 'api/fba-calc/stations', _ => {
        throw new Error('API request made without grass cure percentage set')
      })
      cy.visit(FIRE_BEHAVIOR_CALC_ROUTE)

      cy.getByTestId('add-row').click()

      cy.wait('@getStations')

      const stationCode = 322
      cy.selectFBAStationInDropdown(0, stationCode)

      cy.selectFBAFuelTypeInDropdown(0, FuelTypes.get()['o1a'].friendlyName)
      cy.getByTestId(`fuel-type-dropdown-${0}`)
        .find('input')
        .clear()
      cy.selectFBAFuelTypeInDropdown(0, FuelTypes.get()['o1b'].friendlyName)
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
      cy.visit(FIRE_BEHAVIOR_CALC_ROUTE)

      cy.getByTestId('add-row').click()

      cy.wait('@getStations')

      const stationCode = 322
      cy.selectFBAStationInDropdown(0, stationCode)

      cy.getByTestId('remove-rows').should('not.have.class', 'Mui-disabled')
    })

    it('Rows can be added and removed', () => {
      cy.intercept('GET', 'api/stations/*', { fixture: 'weather-stations.json' }).as('getStations')
      cy.visit(FIRE_BEHAVIOR_CALC_ROUTE)

      cy.getByTestId('add-row').click()

      cy.wait('@getStations')

      const stationCode = 322
      cy.selectFBAStationInDropdown(0, stationCode)

      cy.url().should('contain', `s=${stationCode}`)

      cy.getByTestId('select-all').click()

      cy.getByTestId('remove-rows').click()

      cy.url().should('not.contain', `s=${stationCode}`)
    })
  })
})
