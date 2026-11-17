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
  const files = COVERAGE_FOLDERS.map(folder => path.join(folder, 'coverage-final.json')).filter(file =>
    fs.existsSync(file)
  )
  if (!files.includes(path.join('coverage', 'coverage-final.json'))) {
    throw new Error('Missing Vitest coverage report: coverage/coverage-final.json')
  }

  const mcr = MCR({ outputDir: FINAL_OUTPUT_FOLDER, reports: ['lcov'], cleanCache: true })
  await Promise.all(
    files.map(file => {
      const coverage = fs.readJsonSync(file)
      for (const excluded of EXCLUDE) delete coverage[excluded]
      return mcr.add(coverage)
    })
  )
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
