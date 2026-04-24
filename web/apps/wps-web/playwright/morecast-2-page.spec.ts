import path from 'node:path'
import { test, expect } from './fixtures'

const MORE_CAST_2_ROUTE = '/morecast-2'
const fixturesDir = path.join(import.meta.dirname, 'fixtures')

test.describe('More Cast 2 Page', () => {
  test.beforeEach(async ({ page }) => {
    // Mimic window.Playwright so AuthWrapper calls testAuthenticate() instead of
    // triggering a real Keycloak login-required redirect.
    await page.addInitScript(() => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      ;(globalThis as any).Playwright = {}
    })

    await page.route('**/api/fba/fire-centers', route =>
      route.fulfill({ path: path.join(fixturesDir, 'fba/fire-centers.json') })
    )
  })

  test('Renders the initial page', async ({ page }) => {
    await page.route('**/api/stations/groups', route => route.fulfill({ json: { groups: [] } }))
    await page.goto(MORE_CAST_2_ROUTE)

    await expect(page.getByTestId('station-group-dropdown')).toBeVisible()
    await expect(page.getByTestId('morecast2-data-grid')).toBeVisible()
    await expect(page.getByTestId('morecast2-station-panel')).toBeVisible()
  })

  test('StationGroupDropdown displays groups returned by the API', async ({ page }) => {
    await page.route('**/api/stations/groups', route =>
      route.fulfill({ path: path.join(fixturesDir, 'stations/station-groups.json') })
    )
    await page.goto(MORE_CAST_2_ROUTE)

    const dropdown = page.getByTestId('station-group-dropdown')

    // "Only my groups" is checked by default; the test idir is 'test@idir' (set by
    // AuthWrapper when window.Playwright is truthy), so only the matching group appears.
    await dropdown.getByRole('button', { name: 'Open' }).click()
    await expect(page.getByRole('option', { name: 'My Test Group' })).toBeVisible()
    await expect(page.getByRole('option', { name: 'Another Users Group' })).toHaveCount(0)

    // Unchecking the filter reveals all groups from the API response.
    await page.getByTestId('only-my-groups').click()
    await dropdown.getByRole('button', { name: 'Open' }).click()
    await expect(page.getByRole('option', { name: 'My Test Group' })).toBeVisible()
    await expect(page.getByRole('option', { name: 'Another Users Group' })).toBeVisible()
  })
})
