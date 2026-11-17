import MCR from 'monocart-coverage-reports'
import { coverageOptions } from './coverage-options'

export default async function globalTeardown() {
  const mcr = MCR(coverageOptions)
  if (!mcr.hasCache()) {
    console.log('No Playwright coverage data found — skipping report.')
    return
  }
  // Writes coverage-playwright/coverage-final.json (Istanbul format) for mergeCoverage.cjs
  await mcr.generate()
}
