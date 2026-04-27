import { test as base } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'
import crypto from 'node:crypto'

export type { Page } from '@playwright/test'

const coverageTempDir = path.join(import.meta.dirname, '..', '.nyc_temp_playwright')

export const test = base.extend({
  page: async ({ page }, runTest) => {
    // Mimic window.Playwright so AuthWrapper calls testAuthenticate() instead of
    // triggering a real Keycloak login-required redirect.
    await page.addInitScript(() => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      ;(globalThis as any).Playwright = {}
    })
    await runTest(page)

    // After each test, collect Istanbul coverage from the browser and write to a temp file.
    // vite-plugin-istanbul populates window.__coverage__ when window.Playwright is set.
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const coverage = await page.evaluate(() => (globalThis as any).__coverage__)
    if (coverage) {
      fs.mkdirSync(coverageTempDir, { recursive: true })
      const file = path.join(coverageTempDir, `${crypto.randomUUID()}.json`)
      fs.writeFileSync(file, JSON.stringify(coverage))
    }
  }
})

export { expect } from '@playwright/test'
