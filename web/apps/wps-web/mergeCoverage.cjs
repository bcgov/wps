/**
 * Merges the coverage reports from Playwright, Vitest (wps-web) and the shared packages
 * into a single lcov report in the "finalCoverage" folder.
 */
const path = require('node:path')
const fs = require('fs-extra')
const libCoverage = require('istanbul-lib-coverage')
const libReport = require('istanbul-lib-report')
const reports = require('istanbul-reports')

const FINAL_OUTPUT_FOLDER = 'finalCoverage'
const PACKAGES = ['api', 'ui', 'utils']
const PACKAGE_COVERAGE_FOLDERS = PACKAGES.map(pkg => `../../packages/${pkg}/coverage`)
const COVERAGE_FOLDERS = ['coverage', 'coverage-playwright', ...PACKAGE_COVERAGE_FOLDERS]
// Files left out of the final report
const EXCLUDE = ['src/serviceWorker.ts', 'src/app/store.ts'].map(file => path.resolve(file))

const map = libCoverage.createCoverageMap({})
for (const folder of COVERAGE_FOLDERS) {
  const file = path.join(folder, 'coverage-final.json')
  if (fs.existsSync(file)) {
    map.merge(fs.readJsonSync(file))
  } else if (folder === 'coverage') {
    throw new Error(`Missing Vitest coverage report: ${file}`)
  }
}
map.filter(file => !EXCLUDE.includes(file))

fs.emptyDirSync(FINAL_OUTPUT_FOLDER)
const context = libReport.createContext({ dir: FINAL_OUTPUT_FOLDER, coverageMap: map })
reports.create('lcov').execute(context)

// Clean up — fs.removeSync (fs-extra) is a no-op if the path doesn't exist
for (const folder of COVERAGE_FOLDERS) {
  fs.removeSync(folder)
}
