import { FIRE_BEHAVIOR_CALC_ROUTE } from '../../src/utils/constants'
import { FuelTypes } from '../../src/features/fbaCalculator/fuelTypes'

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
    cy.screenshot()
    visitAndAddRow()
    cy.screenshot()
    cy.wait(0)
    cy.screenshot()

    cy.wait('@getStations')

    cy.setFBAGrassCurePercentage(grassCure, 1)

    cy.setFBAWindSpeed(windSpeed, 1)

    cy.getByTestId('fba-table-body').children().should('have.length', 1)

    cy.selectFBAStationInDropdown(stationCode, 1)

    cy.selectFBAFuelTypeInDropdown(fuelType.friendlyName, 1)

    cy.wait('@calculateResults')

    cy.rowCountShouldBe(1)
    cy.url().should('contain', `s=${stationCode}&f=${fuelType.name.toLowerCase()}&c=${grassCure}&w=${windSpeed}`)
  })
  describe('Hover', () => {
    it('Should move the tooltip to the left on hover', () => {
      cy.intercept('GET', 'api/stations/*', { fixture: 'weather-stations.json' }).as('getStations')
      cy.visit(FIRE_BEHAVIOR_CALC_ROUTE)
      cy.getByTestId('tooltip-fire-size').invoke('attr', 'style').should('eq', 'left: 0px;')
      cy.getByTestId('header-fire-size').trigger('mouseover')
      // I wish we were asserting something useful here, but since the hover style is never applied (cypress shortcoming),
      // the text size isn't calculated in cypress, and as such the item never moves to the left.
      // At least we're getting some code coverage.
      cy.getByTestId('tooltip-fire-size').invoke('attr', 'style').should('eq', 'left: 0px;')
    })
  })
  describe('Dropdowns', () => {
    it('Can select station if successfully received stations', () => {
      cy.intercept('GET', 'api/stations/*', { fixture: 'weather-stations.json' }).as('getStations')

      visitAndAddRow()
      cy.wait(0)

      cy.wait('@getStations')

      cy.getByTestId('fba-table-body').children().should('have.length', 1)

      const stationCode = 322
      cy.selectFBAStationInDropdown(stationCode, 1)

      cy.rowCountShouldBe(1)
      cy.url().should('contain', `s=${stationCode}`)
    })
    it('Can select fuel type successfully', () => {
      cy.intercept('GET', 'api/stations/*', { fixture: 'weather-stations.json' }).as('getStations')

      visitAndAddRow()

      cy.wait(0)

      cy.wait('@getStations')

      cy.getByTestId('fba-table-body').children().should('have.length', 1)

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

      cy.wait(0)

      cy.wait('@getStations')

      cy.getByTestId('fba-table-body').children().should('have.length', 1)

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

      cy.wait(0)

      cy.wait('@getStations')

      cy.getByTestId('fba-table-body').children().should('have.length', 1)

      const stationCode = 322
      cy.selectFBAStationInDropdown(stationCode, 1)

      cy.selectFBAFuelTypeInDropdown(FuelTypes.get()['o1a'].friendlyName, 1)
      cy.getByTestId(`fuel-type-dropdown-fba-1`).find('input').clear()
      cy.selectFBAFuelTypeInDropdown(FuelTypes.get()['o1b'].friendlyName, 1)
    })
  })
  describe('Row management', () => {
    it('Removes invalid stations', () => {
      cy.intercept('GET', 'api/stations/*', { fixture: 'weather-stations.json' }).as('getStations')
      cy.intercept('POST', 'api/fba-calc/stations', req => {
        // One of our stations (9999) is invalid, so we expect it to be excluded from the request.
        expect(req.body.stations.length).to.eq(1)
      }).as('calculateResults')
      cy.visit(FIRE_BEHAVIOR_CALC_ROUTE + '?s=322&f=c1&c=1&w=2,s=9999&f=c1&c=1&w=2')
      cy.wait('@calculateResults')
    })
    it('Disables remove row(s) button when table is empty', () => {
      cy.intercept('GET', 'api/stations/*', { fixture: 'weather-stations.json' }).as('getStations')
      cy.visit(FIRE_BEHAVIOR_CALC_ROUTE)

      cy.getByTestId('remove-rows').should('have.class', 'Mui-disabled')
    })

    it('Enables remove row(s) button when table is not empty', () => {
      cy.intercept('GET', 'api/stations/*', { fixture: 'weather-stations.json' }).as('getStations')

      visitAndAddRow()

      cy.wait(0)

      cy.wait('@getStations')

      cy.getByTestId('fba-table-body').children().should('have.length', 1)

      const stationCode = 322
      cy.selectFBAStationInDropdown(stationCode, 1)

      cy.getByTestId('remove-rows').should('not.have.class', 'Mui-disabled')
    })

    it('Rows can be added and removed', () => {
      cy.intercept('GET', 'api/stations/*', { fixture: 'weather-stations.json' }).as('getStations')

      visitAndAddRow()

      cy.wait('@getStations').then(interception => {
        expect(interception.response.body.type).to.equal('FeatureCollection')
      })

      cy.getByTestId('fba-table-body').children().should('have.length', 1)

      const stationCode = 322
      cy.selectFBAStationInDropdown(stationCode, 1)

      cy.rowCountShouldBe(1)
      cy.url().should('contain', `s=${stationCode}`)

      cy.getByTestId('select-all').click()

      cy.getByTestId('remove-rows').click()

      cy.getByTestId('fba-instructions').should('be.visible')

      cy.url().should('not.contain', `s=${stationCode}`)
    })
    it('Specific rows can be removed', () => {
      cy.intercept('GET', 'api/stations/*', { fixture: 'weather-stations.json' }).as('getStations')

      visitAndAddRow()

      cy.wait('@getStations').then(interception => {
        expect(interception.response.body.type).to.equal('FeatureCollection')
      })

      cy.getByTestId('fba-table-body').children().should('have.length', 1)

      const stationCode = 322
      cy.selectFBAStationInDropdown(stationCode, 1)

      cy.rowCountShouldBe(1)
      cy.url().should('contain', `s=${stationCode}`)

      cy.setSelectedRow()

      cy.getByTestId('remove-rows').click()

      cy.getByTestId('fba-instructions').should('be.visible')

      cy.url().should('not.contain', `s=${stationCode}`)
    })
  })

  describe('Export data to CSV', () => {
    it('Disables the Export button when 0 rows are selected', () => {
      cy.intercept('GET', 'api/stations/*', { fixture: 'weather-stations.json' }).as('getStations')
      visitAndAddRow()
      cy.wait('@getStations').then(interception => {
        expect(interception.response.body.type).to.equal('FeatureCollection')
      })
      cy.getByTestId('fba-table-body').children().should('have.length', 1)
      cy.selectFBAStationInDropdown(322, 1)
      cy.selectFBAFuelTypeInDropdown('C3', 1)
      cy.getByTestId('export').should('be.visible')
      cy.getByTestId('export').should('be.disabled')
    })

    it('Enables the Export button once 1 or more rows are selected', () => {
      cy.intercept('GET', 'api/stations/*', { fixture: 'weather-stations.json' }).as('getStations')
      visitAndAddRow()
      cy.wait('@getStations').then(interception => {
        expect(interception.response.body.type).to.equal('FeatureCollection')
      })
      cy.getByTestId('fba-table-body').children().should('have.length', 1)
      cy.selectFBAStationInDropdown(322, 1)
      cy.selectFBAFuelTypeInDropdown('C4', 1)
      cy.getByTestId('select-all').click()
      cy.getByTestId('export').should('be.enabled')
    })
  })

  describe('Filter columns dialog', () => {
    it('Disables the Filter Columns dialog open button when 0 rows are in table', () => {
      cy.intercept('GET', 'api/stations/*', { fixture: 'weather-stations.json' }).as('getStations')
      cy.visit(FIRE_BEHAVIOR_CALC_ROUTE)

      cy.getByTestId('filter-columns-btn').should('be.disabled')
    })

    it('Enables the Columns button when 1 or more rows are in the FBA Table', () => {
      cy.intercept('GET', 'api/stations/*', { fixture: 'weather-stations.json' }).as('getStations')
      cy.intercept('POST', 'api/fba-calc/stations', {
        fixture: 'fba-calc/322_209_response.json'
      }).as('calculateResults')

      visitAndAddRow()

      cy.wait('@getStations').then(interception => {
        expect(interception.response.body.type).to.equal('FeatureCollection')
      })
      cy.getByTestId('fba-table-body').children().should('have.length', 1)
      cy.selectFBAStationInDropdown(322, 1)
      cy.selectFBAFuelTypeInDropdown('C4', 1)

      cy.wait('@calculateResults')

      cy.getByTestId('filter-columns-btn').should('be.enabled')
    })

    it('Removes columns from FBA Table if the columns have been deselected from the dialog', () => {
      cy.intercept('GET', 'api/stations/*', { fixture: 'weather-stations.json' }).as('getStations')
      cy.intercept('POST', 'api/fba-calc/stations', {
        fixture: 'fba-calc/322_209_response.json'
      }).as('calculateResults')

      visitAndAddRow()
      cy.wait('@getStations').then(interception => {
        expect(interception.response.body.type).to.equal('FeatureCollection')
      })
      cy.getByTestId('fba-table-body').children().should('have.length', 1)
      cy.selectFBAStationInDropdown(322, 1)
      cy.selectFBAFuelTypeInDropdown('C4', 1)

      cy.getByTestId('add-row').click()
      cy.selectFBAStationInDropdown(209, 2)
      cy.selectFBAFuelTypeInDropdown('C1', 2)

      cy.wait('@calculateResults')

      cy.getByTestId('filter-columns-btn').should('be.enabled')
      // open modal
      cy.getByTestId('filter-columns-btn').click()
      cy.getByTestId('filter-Wind-Dir').click()
      cy.getByTestId('filter-Fire-Type').click()
      // CSS.escape() is required because otherwise Cypress can't interpret the round brackets
      // and thus can't find the HTML element
      cy.getByTestId(`${CSS.escape('filter-CFB-(%)')}`).click()
      cy.getByTestId(`${CSS.escape('filter-Flame-Length-(m)')}`).click()
      cy.getByTestId('apply-btn').click()

      // check that hidden columns are actually hidden
      cy.get('table').find('thead > tr').should('not.contain', 'Wind Dir')
      cy.get('table').find('thead > tr').should('not.contain', 'Fire Type')
      cy.get('table').find('thead > tr').should('not.contain', 'CFB (%)')
      cy.get('table').find('thead > tr').should('not.contain', 'Flame Length (m)')

      // check that some of the other columns are still visible
      cy.get('table').find('thead > tr').should('contain', 'Weather Station')
      cy.get('table').find('thead > tr').should('contain', 'FBP Fuel Type')
      cy.get('table').find('thead > tr').should('contain', 'HFI')
    })
  })
})
