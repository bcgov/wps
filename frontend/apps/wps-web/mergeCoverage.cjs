/**
 * This script merges the coverage reports from Playwright and Jest into a single one,
 * inside the "finalCoverage" folder
 *
 * Script adapted from: https://rafaelalmeidatk.com/blog/merging-coverage-reports-from-jest-and-cypress
 */
const { execSync } = require('child_process')
const fs = require('fs-extra')
const PLAYWRIGHT_COVERAGE_FOLDER = 'coverage-playwright'
const JEST_COVERAGE_FOLDER = 'coverage'
const INTERMEDIATE_FOLDER = 'intermediateCoverage'
const FINAL_OUTPUT_FOLDER = 'finalCoverage'
const run = commands => {
  commands.forEach(command => execSync(command, { stdio: 'inherit' }))
}
const PACKAGES = ['api', 'ui', 'utils']

// Create the intermediate folder and move the reports from playwright and jest inside it
fs.emptyDirSync(INTERMEDIATE_FOLDER)
fs.copyFileSync(`${JEST_COVERAGE_FOLDER}/coverage-final.json`, `${INTERMEDIATE_FOLDER}/from-jest.json`)
if (fs.existsSync(`${PLAYWRIGHT_COVERAGE_FOLDER}/coverage-final.json`)) {
  fs.copyFileSync(`${PLAYWRIGHT_COVERAGE_FOLDER}/coverage-final.json`, `${INTERMEDIATE_FOLDER}/from-playwright.json`)
}
PACKAGES.forEach(pkg => {
  const src = `../../packages/${pkg}/coverage/coverage-final.json`
  if (fs.existsSync(src)) {
    fs.copyFileSync(src, `${INTERMEDIATE_FOLDER}/from-${pkg}.json`)
  }
})
fs.emptyDirSync('.nyc_output')
fs.emptyDirSync(FINAL_OUTPUT_FOLDER)
// Run "nyc merge" inside the intermediate folder, merging the two coverage files into one,
// then generate the final report on the coverage folder
run([
  // "nyc merge" will create a "coverage.json" file on the root, we move it to .nyc_output
  `nyc merge ${INTERMEDIATE_FOLDER} && mv coverage.json .nyc_output/out.json`,
  `nyc report --reporter lcov --report-dir ${FINAL_OUTPUT_FOLDER}`
])

// Clean up — fs.removeSync (fs-extra) is a no-op if the path doesn't exist
fs.removeSync(JEST_COVERAGE_FOLDER)
fs.removeSync(PLAYWRIGHT_COVERAGE_FOLDER)
fs.removeSync(INTERMEDIATE_FOLDER)
PACKAGES.forEach(pkg => fs.removeSync(`../../packages/${pkg}/coverage`))
