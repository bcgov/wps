import path from 'node:path'
import { test, expect, type Page } from './fixtures'

const HFI_CALC_ROUTE = '/hfi-calculator'
const fixturesDir = path.join(import.meta.dirname, 'fixtures')
const hfiFixturesDir = path.join(fixturesDir, 'hfi-calc')

async function stubHFI(page: Page, hfiFixture: string, fireCentresFixture = 'fire_centres.json') {
  await page.route('**/api/hfi-calc/fire-centres', route =>
    route.fulfill({ path: path.join(hfiFixturesDir, fireCentresFixture) })
  )
  await page.route('**/api/hfi-calc/fuel_types', route =>
    route.fulfill({ path: path.join(hfiFixturesDir, 'fuel_types.json') })
  )
  // Only intercept GET requests; POST/other requests fall through to more specific handlers
  await page.route('**/api/hfi-calc/fire_centre/**', route => {
    if (route.request().method() === 'GET') {
      route.fulfill({ path: path.join(hfiFixturesDir, hfiFixture) })
    } else {
      route.fallback()
    }
  })
}

async function selectFireCentre(page: Page, name: string) {
  const input = page.getByTestId('fire-centre-dropdown').getByRole('combobox')
  await input.click()
  await input.fill(name)
  const option = page.getByRole('option').first()
  await option.waitFor()
  await option.click()
  await page.getByTestId('hfi-calc-weekly-table').waitFor({ state: 'visible' })
  // Wait for all loading to finish so the backdrop isn't covering the page
  await page.getByTestId('loading-backdrop').waitFor({ state: 'hidden' })
}

test.describe('HFI Calculator Page', () => {
  const start_date = '2021-08-02'
  const end_date = '2021-08-06'

  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      ;(globalThis as any).Playwright = {}
    })
  })

  test.describe('first visit - no selected fire centre', () => {
    test('should show the select fire centre instructions', async ({ page }) => {
      await page.route('**/api/hfi-calc/fire-centres', route =>
        route.fulfill({ path: path.join(hfiFixturesDir, 'fire_centres.json') })
      )
      await page.route('**/api/hfi-calc/fuel_types', route =>
        route.fulfill({ path: path.join(hfiFixturesDir, 'fuel_types.json') })
      )
      await page.goto(HFI_CALC_ROUTE)
      await expect(page.getByTestId('hfi-empty-fire-centre')).toBeVisible()
    })
  })

  test.describe('prep period - saved', () => {
    test.beforeEach(async ({ page }) => {
      await stubHFI(page, 'dailies-saved.json')
      await page.goto(HFI_CALC_ROUTE)
      await selectFireCentre(page, 'Kamloops')
    })

    test('toggle station works', async ({ page }) => {
      await page.route(`**/planning_area/70/station/239/selected/false`, route =>
        route.fulfill({ path: path.join(hfiFixturesDir, 'dailies-disable-station.json') })
      )
      const deselReq = page.waitForRequest(r => r.url().includes('/station/239/selected/false'))
      await page.getByTestId('select-station-239').click()
      await deselReq
      await expect(page.getByTestId('select-station-239').getByRole('checkbox')).not.toBeChecked()

      await page.route(`**/planning_area/70/station/239/selected/true`, route =>
        route.fulfill({ path: path.join(hfiFixturesDir, 'dailies-saved.json') })
      )
      const selReq = page.waitForRequest(r => r.url().includes('/station/239/selected/true'))
      await page.getByTestId('select-station-239').click()
      await selReq
      await expect(page.getByTestId('select-station-239').getByRole('checkbox')).toBeChecked()
      await expect(page.getByTestId('hfi-success-alert')).toBeVisible()
    })

    test('prep period should send a new request to the server', async ({ page }) => {
      const reqPromise = page.waitForRequest(
        r => r.url().includes('/fire_centre/1/2021-08-03/2021-08-07') && r.method() === 'GET'
      )
      // The text field is disabled; click the button wrapper to open the date picker
      await page.getByTestId('date-range-picker-button').click({ force: true })
      await page.getByTestId('date-range-reset-button').waitFor({ state: 'visible' })
      await page.getByTestId('date-range-reset-button').click()
      // Click first day and wait for header to confirm React re-rendered the state update
      await page.getByTestId('day-2021-08-03').getByRole('button').click()
      await expect(page.getByTestId('menu-start-date')).toContainText('August 03, 2021')
      // Now click end day; startDate is now set in state so onChange will fire
      await page.getByTestId('day-2021-08-07').getByRole('button').click()
      await page.keyboard.press('Escape')
      await reqPromise
      await expect(page.getByTestId('hfi-success-alert')).not.toBeAttached()
    })

    test('new fire starts should send a new request to the server', async ({ page }) => {
      await page.route(
        url => url.pathname.includes('/fire_start_range/4'),
        route => route.fulfill({ path: path.join(hfiFixturesDir, 'dailies-saved.json') })
      )
      const reqPromise = page.waitForRequest(r => r.url().includes('/fire_start_range/4') && r.method() === 'POST')
      const fireStartsInput = page.getByTestId('fire-starts-dropdown').first().getByRole('combobox')
      await fireStartsInput.click()
      const option36 = page.getByRole('option', { name: '3-6' })
      await option36.waitFor()
      await option36.click()
      await reqPromise
      await expect(page.getByTestId('hfi-success-alert')).toBeVisible()
    })

    test('set fuel type should send a request to the server', async ({ page }) => {
      await page.route(
        url => url.pathname.includes('/fuel_type/3'),
        route => route.fulfill({ path: path.join(hfiFixturesDir, 'dailies-saved.json') })
      )
      const reqPromise = page.waitForRequest(r => r.url().includes('/fuel_type/3') && r.method() === 'POST')
      const fuelTypeInput = page.getByTestId('fuel-type-dropdown').first().getByRole('combobox')
      await fuelTypeInput.click()
      const c2Option = page.getByRole('option', { name: 'C2' })
      await c2Option.waitFor()
      await c2Option.click()
      await reqPromise
      await expect(page.getByTestId('hfi-success-alert')).toBeVisible()
    })

    test('should switch the tab to prep period from a daily tab when a different fire centre is selected', async ({
      page
    }) => {
      await page.getByTestId('daily-toggle-1').click()
      await expect(page.getByTestId('hfi-calc-daily-table')).toBeVisible()
      await selectFireCentre(page, 'Coastal')
      await expect(page.getByTestId('hfi-calc-daily-table')).not.toBeAttached()
      await expect(page.getByTestId('hfi-calc-weekly-table')).toBeVisible()
    })
  })

  test.describe('default date ranges', () => {
    test.beforeEach(async ({ page }) => {
      await stubHFI(page, 'hfi_result_cariboo.json')
      await page.goto(HFI_CALC_ROUTE)
      await selectFireCentre(page, 'Cariboo')
    })

    test('should load the current HFI Result for a fire centre, regardless of default prep date ranges', async ({
      page
    }) => {
      await expect(page.getByTestId('daily-toggle-0')).toContainText('Fri, Jul 01')
      await expect(page.getByTestId('daily-toggle-3')).toContainText('Mon, Jul 04')

      // Override fire_centre/** with kamloops fixture (registered after, so higher priority)
      await page.route('**/api/hfi-calc/fire_centre/**', route =>
        route.fulfill({ path: path.join(hfiFixturesDir, 'hfi_result_kamloops.json') })
      )
      await selectFireCentre(page, 'Kamloops')

      await expect(page.getByTestId('daily-toggle-0')).toContainText('Fri, Jul 01')
      await expect(page.getByTestId('daily-toggle-2')).toContainText('Sun, Jul 03')
      await expect(page.getByTestId('daily-toggle-3')).not.toBeAttached()
    })
  })

  test.describe('ready states', () => {
    test.beforeEach(async ({ page }) => {
      await stubHFI(page, 'dailies-saved.json')
      // Registered after fire_centre/**, so this more specific handler takes priority (LIFO)
      await page.route(
        url => /\/api\/hfi-calc\/fire_centre\/\d+\/\d{4}-\d{2}-\d{2}\/\d{4}-\d{2}-\d{2}\/ready$/.test(url.pathname),
        route => route.fulfill({ path: path.join(hfiFixturesDir, 'ready-states.json') })
      )
      await page.route(
        url => url.pathname.includes('/planning_area/') && url.pathname.endsWith('/ready'),
        route => route.fulfill({ status: 200, contentType: 'application/json', body: '{}' })
      )
      await page.goto(HFI_CALC_ROUTE)
      await selectFireCentre(page, 'Kamloops')
    })

    test('should toggle off ready state when a station is unselected', async ({ page }) => {
      await page.route(`**/station/239/selected/false`, route =>
        route.fulfill({ path: path.join(hfiFixturesDir, 'dailies-disable-station.json') })
      )
      const toggleReadyPromise = page.waitForRequest(
        r => r.url().includes('/planning_area/') && r.url().endsWith('/ready') && r.method() === 'POST'
      )
      const deselReq = page.waitForRequest(r => r.url().includes('/station/239/selected/false'))
      await page.getByTestId('select-station-239').click()
      await deselReq
      await expect(page.getByTestId('select-station-239').getByRole('checkbox')).not.toBeChecked()
      await expect(page.getByTestId('hfi-success-alert')).toBeVisible()
      await toggleReadyPromise
    })

    test('should toggle off ready state when fire starts is changed', async ({ page }) => {
      await page.route(
        url => url.pathname.includes('/fire_start_range/'),
        route => route.fulfill({ path: path.join(hfiFixturesDir, 'dailies-saved.json') })
      )
      const toggleReadyPromise = page.waitForRequest(
        r => r.url().includes('/planning_area/') && r.url().endsWith('/ready') && r.method() === 'POST'
      )
      const fireStartsInput = page.getByTestId('fire-starts-dropdown').first().getByRole('combobox')
      await fireStartsInput.click()
      const option36 = page.getByRole('option', { name: '3-6' })
      await option36.waitFor()
      await option36.click()
      await expect(page.getByTestId('hfi-success-alert')).toBeVisible()
      await toggleReadyPromise
    })

    test('should toggle off ready state when fuel type is changed', async ({ page }) => {
      await page.route(
        url => url.pathname.includes('/fuel_type/'),
        route => route.fulfill({ path: path.join(hfiFixturesDir, 'dailies-saved.json') })
      )
      const toggleReadyPromise = page.waitForRequest(
        r => r.url().includes('/planning_area/') && r.url().endsWith('/ready') && r.method() === 'POST'
      )
      const fuelTypeInput = page.getByTestId('fuel-type-dropdown').first().getByRole('combobox')
      await fuelTypeInput.click()
      const c2Option = page.getByRole('option', { name: 'C2' })
      await c2Option.waitFor()
      await c2Option.click()
      await expect(page.getByTestId('hfi-success-alert')).toBeVisible()
      await toggleReadyPromise
    })
  })

  test.describe('all data exists', () => {
    test.beforeEach(async ({ page }) => {
      await stubHFI(page, 'dailies.json')
      await page.goto(HFI_CALC_ROUTE)
      await selectFireCentre(page, 'Kamloops')
      await page.getByTestId('daily-toggle-0').click()
    })

    test('should display Daily View Table after clicking on daily button', async ({ page }) => {
      await expect(page.getByTestId('hfi-calc-daily-table')).toBeVisible()
    })

    test('should have at least 15 rows in Daily Table View', async ({ page }) => {
      const rowCount = await page.getByTestId('hfi-calc-daily-table').locator('tr').count()
      expect(rowCount).toBeGreaterThanOrEqual(15)
    })

    test('should display weather results, intensity groups, & prep levels in Daily View Table', async ({ page }) => {
      await expect(page.getByTestId('239-hfi')).toContainText('25.8')
      await expect(page.getByTestId('239-ros')).toContainText('0.0')
      await expect(page.getByTestId('239-1-hr-size')).toContainText('0.0')
      await expect(page.getByTestId('239-fire-type')).toContainText('SUR')
      await expect(page.getByTestId('239-intensity-group')).toContainText('1')
      await expect(page.getByTestId('zone-70-mean-intensity')).toContainText('1')
      await expect(page.getByTestId('daily-prep-level-70')).toContainText('1')
      await expect(page.getByTestId('daily-prep-level-70')).toHaveClass(/prepLevel1/)
      await expect(page.getByTestId('daily-prep-level-71')).toContainText('3')
      await expect(page.getByTestId('daily-prep-level-71')).toHaveClass(/prepLevel3/)
    })

    test('download should hit pdf download url', async ({ page }) => {
      await page.route(
        url => url.pathname === `/api/hfi-calc/fire_centre/1/${start_date}/${end_date}/pdf`,
        route => route.fulfill({ status: 200, contentType: 'application/pdf', body: Buffer.from('PDF') })
      )
      const reqPromise = page.waitForRequest(
        r => r.url().includes(`/fire_centre/1/${start_date}/${end_date}/pdf`) && r.method() === 'GET'
      )
      await page.getByTestId('download-pdf-button').click()
      await reqPromise
    })
  })

  test.describe('dailies data are missing', () => {
    test.beforeEach(async ({ page }) => {
      await stubHFI(page, 'dailies-missing.json')
      await page.goto(HFI_CALC_ROUTE)
      await selectFireCentre(page, 'Kamloops')
      await page.getByTestId('daily-toggle-0').click()
    })

    test('should display error icon for mean intensity group in Daily View Table', async ({ page }) => {
      await expect(page.getByTestId('306-ros')).toBeEmpty()
      await expect(page.getByTestId('306-hfi')).toBeEmpty()
      await expect(page.getByTestId('306-1-hr-size')).toBeEmpty()
      await expect(page.getByTestId('306-intensity-group')).toBeEmpty()
      await page.getByTestId('zone-74-mig-error').scrollIntoViewIfNeeded()
      await expect(page.getByTestId('zone-74-mig-error')).toBeVisible()
    })
  })

  test.describe('high intensity', () => {
    test.beforeEach(async ({ page }) => {
      await stubHFI(page, 'dailies-high-intensity.json', 'fire-centres-minimal.json')
      await page.goto(HFI_CALC_ROUTE)
      await selectFireCentre(page, 'Kamloops')
      await page.getByTestId('daily-toggle-0').click()
    })

    test('should show highest intensity values for mean intensity group in Daily View Table', async ({ page }) => {
      await expect(page.getByTestId('306-intensity-group')).toContainText('5')
      await expect(page.getByTestId('zone-74-mean-intensity')).toContainText('5')
    })
  })

  test.describe('hfi api endpoint error handling', () => {
    test.beforeEach(async ({ page }) => {
      await stubHFI(page, 'dailies.json')
      await page.goto(HFI_CALC_ROUTE)
      await selectFireCentre(page, 'Kamloops')
    })

    for (const statusCode of [500, 401, 404]) {
      test(`should notify user if endpoint request fails with ${statusCode}`, async ({ page }) => {
        // Register error route (registered after stubHFI, so higher LIFO priority)
        await page.route('**/api/hfi-calc/fire_centre/**', route => route.fulfill({ status: statusCode }))
        // Select Coastal (a different fire centre) to trigger a new fire_centre/** fetch
        const input = page.getByTestId('fire-centre-dropdown').getByRole('combobox')
        await input.click()
        await input.fill('Coastal')
        const option = page.getByRole('option').first()
        await option.waitFor()
        await option.click()
        await expect(page.getByTestId('hfi-error-alert')).toBeVisible()
      })
    }
  })

  test.describe('fire centres api endpoint error handling', () => {
    for (const statusCode of [500, 401, 404]) {
      test(`should notify user if endpoint request fails with ${statusCode}`, async ({ page }) => {
        await page.route('**/api/hfi-calc/fire-centres', route => route.fulfill({ status: statusCode }))
        await page.route('**/api/hfi-calc/fuel_types', route =>
          route.fulfill({ path: path.join(hfiFixturesDir, 'fuel_types.json') })
        )
        await page.goto(HFI_CALC_ROUTE)
        await expect(page.getByTestId('hfi-error-alert')).toBeVisible()
      })
    }
  })
})
