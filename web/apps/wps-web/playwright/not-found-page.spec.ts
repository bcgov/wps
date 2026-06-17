import { expect, test } from './fixtures'

test.describe('Not Found Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/notfound')
  })

  test('Basic Page', async ({ page }) => {
    await expect(page.getByText('Page Not Found')).toBeVisible()
  })
})
