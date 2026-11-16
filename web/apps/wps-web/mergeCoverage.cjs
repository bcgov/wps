/**
 * Merges the coverage reports from Playwright, Vitest (wps-web) and the shared packages
 * into a single lcov report in the "finalCoverage" folder.
 */
const path = require('node:path')
const fs = require('fs-extra')
const { default: MCR } = require('monocart-coverage-reports')

const FINAL_OUTPUT_FOLDER = 'finalCoverage'
const PACKAGES = ['api', 'ui', 'utils']
const PACKAGE_COVERAGE_FOLDERS = PACKAGES.map(pkg => `../../packages/${pkg}/coverage`)
const COVERAGE_FOLDERS = ['coverage', 'coverage-playwright', ...PACKAGE_COVERAGE_FOLDERS]
// Files left out of the final report
const EXCLUDE = new Set(['src/serviceWorker.ts', 'src/app/store.ts'].map(file => path.resolve(file)))

async function main() {
  const mcr = MCR({ outputDir: FINAL_OUTPUT_FOLDER, reports: ['lcov'], cleanCache: true })
  for (const folder of COVERAGE_FOLDERS) {
    const file = path.join(folder, 'coverage-final.json')
    if (!fs.existsSync(file)) {
      if (folder === 'coverage') throw new Error(`Missing Vitest coverage report: ${file}`)
      continue
    }
    const coverage = fs.readJsonSync(file)
    for (const excluded of EXCLUDE) delete coverage[excluded]
    await mcr.add(coverage)
  }
  await mcr.generate()

  // Clean up — fs.removeSync (fs-extra) is a no-op if the path doesn't exist
  for (const folder of COVERAGE_FOLDERS) {
    fs.removeSync(folder)
  }
}

main().catch(error => {
  console.error(error)
  process.exit(1)
})
