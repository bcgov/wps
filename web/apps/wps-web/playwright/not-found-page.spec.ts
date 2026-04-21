import { test, expect } from '@playwright/test'

test.describe('Not Found Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/notfound')
  })

  test('Basic Page', async ({ page }) => {
    await expect(page.getByText('Page Not Found')).toBeVisible()
  })
})
