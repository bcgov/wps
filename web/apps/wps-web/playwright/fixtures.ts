import { test as base } from '@playwright/test'
import MCR from 'monocart-coverage-reports'
import { coverageOptions } from './coverage-options'

export type { Page } from '@playwright/test'

export const test = base.extend({
  page: async ({ page }, runTest) => {
    // Mimic window.Playwright so AuthWrapper calls testAuthenticate() instead of
    // triggering a real Keycloak login-required redirect.
    await page.addInitScript(() => {
      ;(globalThis as any).Playwright = {}
    })

    // Collect native V8 coverage from Chromium; global.teardown merges it into a report.
    await page.coverage.startJSCoverage({ resetOnNavigation: false })
    try {
      await runTest(page)
    } finally {
      const coverage = await page.coverage.stopJSCoverage()
      await MCR(coverageOptions).add(coverage)
    }
  }
})

export { expect } from '@playwright/test'
