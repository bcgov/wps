import path from 'node:path'
import { test, expect, type Page } from './fixtures'

const FBA_ROUTE = '/fire-behaviour-calculator'
const fixturesDir = path.join(import.meta.dirname, 'fixtures')

// Inlined from FuelTypes.get() to avoid cross-tsconfig imports
const C1 = { name: 'C1', friendlyName: 'C1', percentage_conifer: 100, crown_base_height: 2 }

// ---- interaction helpers ----

async function addRow(page: Page) {
  await page.getByTestId('add-row').click()
}

async function selectStation(page: Page, code: number | string, rowId: number) {
  const input = page.getByTestId(`weather-station-dropdown-fba-${rowId}`).getByRole('combobox')
  await input.click()
  await input.fill(String(code))
  await page.getByRole('option').first().waitFor()
  await input.press('Enter')
}

async function selectFuelType(page: Page, fuelType: string, rowId: number) {
  const input = page.getByTestId(`fuel-type-dropdown-fba-${rowId}`).getByRole('combobox')
  await input.click()
  await input.fill(fuelType)
  await page.getByRole('option').first().waitFor()
  await input.press('Enter')
}

async function setGrassCure(page: Page, value: string, rowId: number) {
  const input = page.getByTestId(`grassCureInput-fba-${rowId}`).locator('input')
  await input.fill(value)
  await input.press('Enter')
}

async function setWindSpeed(page: Page, value: string, rowId: number) {
  await page.getByTestId(`windSpeedInput-fba-${rowId}`).locator('input').fill(value)
}

async function expectRowCount(page: Page, count: number) {
  await expect(page.getByTestId('fba-table-body').locator('tr')).toHaveCount(count)
}

async function expectGrassCureForRow(page: Page, value: string, rowId: number) {
  await expect(page.getByTestId(`grassCureInput-fba-${rowId}`).locator('input')).toHaveValue(value)
}

async function expectWindSpeedForRow(page: Page, value: string, rowId: number) {
  await expect(page.getByTestId(`windSpeedInput-fba-${rowId}`).locator('input')).toHaveValue(value)
}

async function expectStationForRow(page: Page, code: string, rowId: number) {
  await expect(page.getByTestId(`weather-station-dropdown-fba-${rowId}`).locator('input')).toHaveValue(new RegExp(code))
}

async function expectFuelTypeForRow(page: Page, fuelType: string, rowId: number) {
  const input = page.getByTestId(`fuel-type-dropdown-fba-${rowId}`).locator('input')
  if (fuelType === '') {
    await expect(input).toHaveValue('')
  } else {
    await expect(input).toHaveValue(new RegExp(fuelType, 'i'))
  }
}

// ---- tests ----

test.describe('FireCalc Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.route(
      url => url.pathname === '/api/stations/',
      route => route.fulfill({ path: path.join(fixturesDir, 'weather-stations.json') })
    )
  })

  test('Sets all input fields and sends correct data to backend', async ({ page }) => {
    const stationCode = 322
    const grassCure = '1'
    const windSpeed = '2'

    await page.route('**/api/fba-calc/stations', route => route.fulfill({ json: { date: '', stations: [] } }))
    const calcRequest = page.waitForRequest(r => r.url().includes('/api/fba-calc/stations') && r.method() === 'POST')

    await page.goto(FBA_ROUTE)
    await addRow(page)
    await setGrassCure(page, grassCure, 1)
    await setWindSpeed(page, windSpeed, 1)
    await selectStation(page, stationCode, 1)
    await selectFuelType(page, C1.friendlyName, 1)

    const body = (await calcRequest).postDataJSON() as { stations: Record<string, unknown>[] }
    expect(body.stations[0]).toMatchObject({
      station_code: stationCode,
      fuel_type: C1.name,
      percentage_conifer: C1.percentage_conifer,
      crown_base_height: C1.crown_base_height,
      grass_cure: Number.parseInt(grassCure)
    })
    await expectRowCount(page, 1)
    await expect(page).toHaveURL(new RegExp(`s=${stationCode}&f=${C1.name.toLowerCase()}&c=${grassCure}`))
  })

  test('Sends wind speed to backend but does not persist it to URL', async ({ page }) => {
    const stationCode = 322
    const grassCure = '1'
    const windSpeed = '2'

    await page.route('**/api/fba-calc/stations', route => route.fulfill({ json: { date: '', stations: [] } }))
    const calcRequest = page.waitForRequest(r => r.url().includes('/api/fba-calc/stations') && r.method() === 'POST')

    await page.goto(FBA_ROUTE)
    await addRow(page)
    await setGrassCure(page, grassCure, 1)
    await setWindSpeed(page, windSpeed, 1)
    await selectStation(page, stationCode, 1)
    await selectFuelType(page, C1.friendlyName, 1)

    const body = (await calcRequest).postDataJSON() as { stations: Record<string, unknown>[] }
    expect(body.stations[0]).toMatchObject({
      station_code: stationCode,
      fuel_type: C1.name,
      percentage_conifer: C1.percentage_conifer,
      crown_base_height: C1.crown_base_height,
      grass_cure: Number.parseInt(grassCure),
      wind_speed: Number.parseFloat(windSpeed)
    })
    await expectRowCount(page, 1)
    await expect(page).toHaveURL(new RegExp(`s=${stationCode}&f=${C1.name.toLowerCase()}&c=${grassCure}`))
    await expect(page).not.toHaveURL(/w=/)
  })

  test.describe('Dropdowns', () => {
    test('Can select station if successfully received stations', async ({ page }) => {
      await page.route('**/api/fba-calc/stations', route => route.fulfill({ json: { date: '', stations: [] } }))

      await page.goto(FBA_ROUTE)
      await addRow(page)
      await setGrassCure(page, '1', 1)
      await selectStation(page, 322, 1)
      await expectRowCount(page, 1)
      await expect(page).toHaveURL(/s=322/)
    })

    test('Can select fuel type successfully', async ({ page }) => {
      await page.route('**/api/fba-calc/stations', route => route.fulfill({ json: { date: '', stations: [] } }))

      await page.goto(FBA_ROUTE)
      await addRow(page)
      await setGrassCure(page, '1', 1)
      await selectFuelType(page, C1.friendlyName, 1)
      await expectRowCount(page, 1)
      await expect(page).toHaveURL(new RegExp(`f=${C1.name.toLowerCase()}`))
    })

    test('Calls backend when station and non-grass fuel type are set', async ({ page }) => {
      await page.route('**/api/fba-calc/stations', route => route.fulfill({ json: { date: '', stations: [] } }))
      const calcRequest = page.waitForRequest(r => r.url().includes('/api/fba-calc/stations') && r.method() === 'POST')

      await page.goto(FBA_ROUTE)
      await addRow(page)
      await setGrassCure(page, '1', 1)
      await selectStation(page, 322, 1)
      await selectFuelType(page, C1.friendlyName, 1)

      const body = (await calcRequest).postDataJSON() as { stations: Record<string, unknown>[] }
      expect(body.stations[0]).toMatchObject({
        station_code: 322,
        fuel_type: C1.name,
        percentage_conifer: C1.percentage_conifer,
        crown_base_height: C1.crown_base_height
      })
      await expectRowCount(page, 1)
      await expect(page).toHaveURL(new RegExp(`s=322&f=${C1.name.toLowerCase()}`))
    })

    test('Does not call backend when grass fuel type is set without grass cure percentage', async ({ page }) => {
      let backendCalled = false
      await page.route('**/api/fba-calc/stations', route => {
        backendCalled = true
        return route.fulfill({ json: { date: '', stations: [] } })
      })

      await page.goto(FBA_ROUTE)
      await addRow(page)
      await setGrassCure(page, '1', 1)
      await selectStation(page, 322, 1)
      await selectFuelType(page, 'O1A', 1)
      await page.getByTestId('fuel-type-dropdown-fba-1').locator('input').clear()
      await selectFuelType(page, 'O1B', 1)

      expect(backendCalled).toBe(false)
    })
  })

  test.describe('Row management', () => {
    test('Removes invalid stations', async ({ page }) => {
      await page.route('**/api/fba-calc/stations', route => route.fulfill({ json: { date: '', stations: [] } }))
      const calcRequest = page.waitForRequest(r => r.url().includes('/api/fba-calc/stations') && r.method() === 'POST')

      await page.goto(`${FBA_ROUTE}?s=322&f=c1&c=1,s=9999&f=c1&c=1`)

      const body = (await calcRequest).postDataJSON() as { stations: unknown[] }
      expect(body.stations.length).toBe(1)
    })

    test('Disables remove row(s) button when table is empty', async ({ page }) => {
      await page.goto(FBA_ROUTE)
      await expect(page.getByTestId('remove-rows')).toBeDisabled()
    })

    test('Enables remove row(s) button when table is not empty', async ({ page }) => {
      await page.route('**/api/fba-calc/stations', route => route.fulfill({ json: { date: '', stations: [] } }))

      await page.goto(FBA_ROUTE)
      await addRow(page)
      await setGrassCure(page, '1', 1)
      await selectStation(page, 322, 1)
      await expect(page.getByTestId('remove-rows')).not.toBeDisabled()
    })

    test('Rows can be added and removed', async ({ page }) => {
      await page.route('**/api/fba-calc/stations', route => route.fulfill({ json: { date: '', stations: [] } }))

      await page.goto(FBA_ROUTE)
      await addRow(page)
      await setGrassCure(page, '1', 1)
      await selectStation(page, 322, 1)
      await expectRowCount(page, 1)
      await expect(page).toHaveURL(/s=322/)
      await page.getByTestId('select-all').click()
      await page.getByTestId('remove-rows').click()
      await expect(page.getByTestId('fba-instructions')).toBeVisible()
      await expect(page).not.toHaveURL(/s=322/)
    })

    test('Specific rows can be removed', async ({ page }) => {
      await page.route('**/api/fba-calc/stations', route => route.fulfill({ json: { date: '', stations: [] } }))

      await page.goto(FBA_ROUTE)
      await addRow(page)
      await setGrassCure(page, '1', 1)
      await selectStation(page, 322, 1)
      await expectRowCount(page, 1)
      await expect(page).toHaveURL(/s=322/)
      await page.getByTestId('selection-checkbox-fba').click()
      await page.getByTestId('remove-rows').click()
      await expect(page.getByTestId('fba-instructions')).toBeVisible()
      await expect(page).not.toHaveURL(/s=322/)
    })

    test('Loads one row from query parameters', async ({ page }) => {
      await page.route('**/api/fba-calc/stations', route => route.fulfill({ json: { date: '', stations: [] } }))

      await page.goto(`${FBA_ROUTE}?s=322&f=c2&c=80`)
      await expectRowCount(page, 1)
      await expectGrassCureForRow(page, '80', 0)
      await expectStationForRow(page, '322', 0)
      await expectFuelTypeForRow(page, 'c2', 0)
    })

    test('Does not load wind speed into row from query parameters', async ({ page }) => {
      await page.route('**/api/fba-calc/stations', route => route.fulfill({ json: { date: '', stations: [] } }))

      await page.goto(`${FBA_ROUTE}?s=322&f=c2&c=80&w=5`)
      await expectRowCount(page, 1)
      await expectWindSpeedForRow(page, '', 0)
      await expectGrassCureForRow(page, '80', 0)
      await expectStationForRow(page, '322', 0)
      await expectFuelTypeForRow(page, 'c2', 0)
    })

    test('Loads multiple rows from query parameters', async ({ page }) => {
      await page.route('**/api/fba-calc/stations', route => route.fulfill({ json: { date: '', stations: [] } }))

      await page.goto(`${FBA_ROUTE}?s=838&f=c3&c=90,s=322&f=c4&c=85`)
      await expectRowCount(page, 2)
      await expectWindSpeedForRow(page, '', 0)
      await expectGrassCureForRow(page, '90', 0)
      await expectStationForRow(page, '838', 0)
      await expectFuelTypeForRow(page, 'c3', 0)
      await expectWindSpeedForRow(page, '', 1)
      await expectGrassCureForRow(page, '85', 1)
      await expectStationForRow(page, '322', 1)
      await expectFuelTypeForRow(page, 'c4', 1)
    })

    test('Handles undefined value for query parameters', async ({ page }) => {
      await page.route('**/api/fba-calc/stations', route => route.fulfill({ json: { date: '', stations: [] } }))

      await page.goto(`${FBA_ROUTE}?s=322&f=undefined&c=undefined`)
      await expectRowCount(page, 1)
      await expectWindSpeedForRow(page, '', 0)
      await expectGrassCureForRow(page, '', 0)
      await expectStationForRow(page, '322', 0)
      await expectFuelTypeForRow(page, '', 0)
    })
  })

  test.describe('Export data to CSV', () => {
    test('Disables the Export button when 0 rows are selected', async ({ page }) => {
      await page.route('**/api/fba-calc/stations', route => route.fulfill({ json: { date: '', stations: [] } }))

      await page.goto(FBA_ROUTE)
      await addRow(page)
      await setGrassCure(page, '1', 1)
      await selectStation(page, 322, 1)
      await selectFuelType(page, 'C3', 1)
      await expect(page.getByTestId('export')).toBeVisible()
      await expect(page.getByTestId('export')).toBeDisabled()
    })

    test('Enables the Export button once 1 or more rows are selected', async ({ page }) => {
      await page.route('**/api/fba-calc/stations', route => route.fulfill({ json: { date: '', stations: [] } }))

      await page.goto(FBA_ROUTE)
      await addRow(page)
      await setGrassCure(page, '1', 1)
      await selectStation(page, 322, 1)
      await selectFuelType(page, 'C4', 1)
      await page.getByTestId('select-all').click()
      await expect(page.getByTestId('export')).toBeEnabled()
    })
  })

  test.describe('Filter columns dialog', () => {
    test('Disables the Filter Columns dialog open button when 0 rows are in table', async ({ page }) => {
      await page.goto(FBA_ROUTE)
      await expect(page.getByTestId('filter-columns-btn')).toBeDisabled()
    })

    test('Enables the Columns button when 1 or more rows are in the FBA Table', async ({ page }) => {
      await page.route('**/api/fba-calc/stations', route =>
        route.fulfill({ path: path.join(fixturesDir, 'fba-calc/322_209_response.json') })
      )

      await page.goto(FBA_ROUTE)
      await addRow(page)
      await setGrassCure(page, '1', 1)
      await selectStation(page, 322, 1)
      await selectFuelType(page, 'C4', 1)
      await page.waitForResponse(r => r.url().includes('/api/fba-calc/stations'))
      await expect(page.getByTestId('filter-columns-btn')).toBeEnabled()
    })

    test('Removes columns from FBA Table when deselected from the dialog', async ({ page }) => {
      await page.route('**/api/fba-calc/stations', route =>
        route.fulfill({ path: path.join(fixturesDir, 'fba-calc/322_209_response.json') })
      )

      await page.goto(FBA_ROUTE)
      await addRow(page)
      await setGrassCure(page, '1', 1)
      await selectStation(page, 322, 1)
      await selectFuelType(page, 'C4', 1)

      await addRow(page)
      await setGrassCure(page, '1', 1)
      await selectStation(page, 209, 2)
      await selectFuelType(page, 'C1', 2)

      await page.waitForResponse(r => r.url().includes('/api/fba-calc/stations'))
      await expect(page.getByTestId('filter-columns-btn')).toBeEnabled()

      await page.getByTestId('filter-columns-btn').click()
      await page.getByTestId('filter-Wind-Dir').click()
      await page.getByTestId('filter-Fire-Type').click()
      await page.getByTestId('filter-CFB-(%)').click()
      await page.getByTestId('filter-Flame-Length-(m)').click()
      await page.getByTestId('apply-btn').click()

      const thead = page.locator('table thead tr')
      await expect(thead).not.toContainText('Wind Dir')
      await expect(thead).not.toContainText('Fire Type')
      await expect(thead).not.toContainText('CFB (%)')
      await expect(thead).not.toContainText('Flame Length (m)')
      await expect(thead).toContainText('Weather Station')
      await expect(thead).toContainText('FBP Fuel Type')
      await expect(thead).toContainText('HFI')
    })
  })
})
