import { FIRE_BEHAVIOR_CALC_ROUTE } from '../../src/utils/constants'
import { FuelTypes } from '../../src/features/fbaCalculator/fuelTypes'
import { DateTime } from 'luxon'

describe('FireBAT Calculator Page', () => {
  describe('Dropdowns', () => {
    it('Can select station if successfully received stations', () => {
      cy.intercept('GET', 'api/stations/*', { fixture: 'weather-stations.json' }).as('getStations')
      cy.intercept('POST', 'api/fba-calc/stations', _ => {
        /* Request should not be made when only station is set */
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
        /* Request should not be made when only fuel type is set */
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
        assert.deepEqual(req.body, {
          stations: [
            {
              date: DateTime.now()
                .toISODate()
                .slice(0, 10),
              station_code: stationCode,
              fuel_type: fuelType.name,
              percentage_conifer: fuelType.percentage_conifer,
              grass_cure: null,
              crown_base_height: fuelType.crown_base_height,
              wind_speed: null
            }
          ]
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
  })
})
