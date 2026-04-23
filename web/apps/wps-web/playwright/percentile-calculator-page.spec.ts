import path from 'node:path'
import { test, expect, type Page } from './fixtures'

const PERCENTILE_CALC_ROUTE = '/percentile-calculator'
const STATION_CODE_QUERY_KEY = 'codes'
const fixturesDir = path.join(import.meta.dirname, 'fixtures')

async function stubStations(page: Page) {
  await page.route(
    url => url.pathname.startsWith('/api/stations/'),
    route => route.fulfill({ path: path.join(fixturesDir, 'weather-stations.json') })
  )
}

async function acceptDisclaimer(page: Page) {
  await page.getByTestId('disclaimer-accept-button').click()
}

async function selectStation(page: Page, code: number | string) {
  const input = page.getByTestId('weather-station-dropdown').getByRole('combobox')
  await input.click()
  await input.fill(String(code))
  const option = page.getByRole('option').first()
  await option.waitFor()
  await option.click()
}

test.describe('Percentile Calculator Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      ;(globalThis as any).Cypress = {}
    })
  })

  test.describe('Weather station dropdown', () => {
    test('Renders error message when fetching stations failed', async ({ page }) => {
      await page.route(
        url => url.pathname.startsWith('/api/stations/'),
        route => route.fulfill({ status: 404, body: 'error' })
      )
      await page.goto(PERCENTILE_CALC_ROUTE)
      await acceptDisclaimer(page)

      await expect(page.getByTestId('error-message')).toContainText('Error occurred (while fetching weather stations).')
    })

    test('Can select & deselect stations if successfully received stations', async ({ page }) => {
      await stubStations(page)
      await page.goto(PERCENTILE_CALC_ROUTE)
      await acceptDisclaimer(page)

      // Select a station by name, then deselect via chip delete
      await selectStation(page, 'AFTON')
      await page.locator('.MuiChip-deleteIcon').click()

      // Select 4 stations — component enforces a max of 3
      const stationCodes = [1275, 322, 209, 838]
      for (const code of stationCodes) {
        await selectStation(page, code)
      }
      await expect(page.locator('.MuiChip-deletable')).toHaveCount(3)

      // Calculate button updates the URL with the first 3 codes
      await page.getByTestId('calculate-percentiles-button').click()
      await expect(page).toHaveURL(new RegExp(`${STATION_CODE_QUERY_KEY}=${stationCodes.slice(0, 3).join(',')}`))
    })

    test('Should let users know if there were invalid weather stations', async ({ page }) => {
      const invalidCodes = [1, 999]
      await stubStations(page)
      await page.route('**/api/percentiles/', route => route.fulfill({ status: 500 }))
      await page.goto(`${PERCENTILE_CALC_ROUTE}?${STATION_CODE_QUERY_KEY}=${invalidCodes.join(',')}`)
      await acceptDisclaimer(page)

      // Page auto-calculates with URL codes, so there may be multiple error-message elements;
      // filter to the one we care about to avoid strict-mode violations.
      const unknownCodeError = page
        .getByTestId('error-message')
        .filter({ hasText: 'Unknown weather station code(s) detected.' })
      await expect(unknownCodeError).toBeVisible()
      await expect(page.getByTestId('weather-station-dropdown')).toContainText(`Unknown (${invalidCodes[0]})`)

      // Remove first unknown station
      await page.locator('.MuiChip-deleteIcon').first().click()
      await expect(page.getByTestId('weather-station-dropdown')).toContainText(`Unknown (${invalidCodes[1]})`)

      // Remove second unknown station — unknown-codes error should disappear
      await page.locator('.MuiChip-deleteIcon').click()
      await expect(unknownCodeError).not.toBeAttached()
    })
  })

  test.describe('Other inputs', () => {
    test.beforeEach(async ({ page }) => {
      await stubStations(page)
      await page.goto(PERCENTILE_CALC_ROUTE)
      await acceptDisclaimer(page)
    })

    test('Percentile textfield should have a value of 90', async ({ page }) => {
      const input = page.getByTestId('percentile-textfield').getByRole('textbox')
      await expect(input).toHaveValue('90')
      await expect(input).toBeDisabled()
    })

    test('Time range slider can select the range between 10 and 30', async ({ page }) => {
      const stationCode = 838
      const slider = page.getByRole('slider', { name: 'Time Range' })

      // Default value is 10
      await expect(slider).toHaveAttribute('aria-valuenow', '10')

      // Select 20 years and check the slider reflects it
      await page.locator('.MuiSlider-markLabel').filter({ hasText: /^20$/ }).click()
      await expect(slider).toHaveAttribute('aria-valuenow', '20')

      // Select 30 years (max) and check the slider reflects it
      await page.locator('.MuiSlider-markLabel').filter({ hasText: /^30$/ }).click()
      await expect(slider).toHaveAttribute('aria-valuenow', '30')

      // Clicking 0 should do nothing — onChange ignores the zero value
      await page.locator('.MuiSlider-markLabel').filter({ hasText: /^0$/ }).click()
      await expect(slider).toHaveAttribute('aria-valuenow', '30')

      await page.route('**/api/percentiles/', route =>
        route.fulfill({ path: path.join(fixturesDir, 'percentiles/percentile-result.json') })
      )
      await selectStation(page, stationCode)

      // Calculate sends year_range derived from timeRange=30: start = 2023-(30-1) = 1994, end = 2023
      const reqPromise = page.waitForRequest(r => r.url().includes('/api/percentiles/') && r.method() === 'POST')
      await page.getByTestId('calculate-percentiles-button').click()
      const req = await reqPromise
      expect(req.postDataJSON()).toEqual({
        stations: [stationCode],
        year_range: { start: 1994, end: 2023 },
        percentile: 90
      })
    })
  })

  test.describe('Calculation result', () => {
    test.beforeEach(async ({ page }) => {
      await stubStations(page)
      await page.goto(PERCENTILE_CALC_ROUTE)
      await acceptDisclaimer(page)
    })

    test('Failed due to network error', async ({ page }) => {
      await page.route('**/api/percentiles/', route => route.fulfill({ status: 404, body: 'error' }))

      await expect(page.getByTestId('calculate-percentiles-button')).toBeDisabled()

      await selectStation(page, 322)

      await page.getByTestId('calculate-percentiles-button').click()
      await expect(page.getByTestId('error-message')).toContainText(
        'Error occurred (while getting the calculation result).'
      )
    })

    test('Successful with one station', async ({ page }) => {
      const stationCode = 838
      await page.route('**/api/percentiles/', route =>
        route.fulfill({ path: path.join(fixturesDir, 'percentiles/percentile-result.json') })
      )

      await selectStation(page, stationCode)

      const reqPromise = page.waitForRequest(r => r.url().includes('/api/percentiles/') && r.method() === 'POST')
      await page.getByTestId('calculate-percentiles-button').click()
      const req = await reqPromise
      expect(req.postDataJSON()).toEqual({
        stations: [stationCode],
        year_range: { start: 2014, end: 2023 },
        percentile: 90
      })

      // Mean table shouldn't be shown
      await expect(page.getByTestId('percentile-mean-result-table')).not.toBeAttached()

      // One percentile table should be shown
      await expect(page.getByTestId('percentile-station-result-table')).toHaveCount(1)

      // Check values in the table
      await expect(page.getByText('Station Name').locator('+ *')).toContainText(`AKOKLI CREEK (${stationCode})`)
      await expect(page.getByTestId('percentile-station-result-FFMC')).toContainText('Not available')
      await expect(page.getByTestId('percentile-station-result-BUI')).toContainText('Not available')
      await expect(page.getByTestId('percentile-station-result-ISI')).toContainText('Not available')
    })

    test('Successful with two stations', async ({ page }) => {
      const stationCodes = [322, 1275]
      await page.route('**/api/percentiles/', route =>
        route.fulfill({ path: path.join(fixturesDir, 'percentiles/two-percentiles-result.json') })
      )

      // Select two weather stations
      for (const code of stationCodes) {
        await selectStation(page, code)
      }

      const reqPromise = page.waitForRequest(r => r.url().includes('/api/percentiles/') && r.method() === 'POST')
      await page.getByTestId('calculate-percentiles-button').click()
      const req = await reqPromise
      expect(req.postDataJSON()).toEqual({
        stations: stationCodes,
        year_range: { start: 2014, end: 2023 },
        percentile: 90
      })

      // Mean table & two percentile tables should be shown
      await expect(page.getByTestId('percentile-mean-result-table')).toBeVisible()
      await expect(page.getByTestId('percentile-station-result-table')).toHaveCount(2)

      // Results should disappear after clicking the reset button
      await page.getByTestId('reset-percentiles-button').click()
      await expect(page.getByTestId('percentile-mean-result-table')).not.toBeAttached()
      await expect(page.getByTestId('percentile-station-result-table')).toHaveCount(0)
    })
  })
})
