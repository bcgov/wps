/**
 * This script merges the coverage reports from Cypress and Jest into a single one,
 * inside the "finalCoverage" folder
 *
 * Script adapted from: https://rafaelalmeidatk.com/blog/merging-coverage-reports-from-jest-and-cypress
 */
const { execSync } = require('child_process')
const fs = require('fs-extra')
const CYPRESS_COVERAGE_FOLDER = 'coverage-cypress'
const JEST_COVERAGE_FOLDER = 'coverage'
const INTERMEDIATE_FOLDER = 'intermediateCoverage'
const FINAL_OUTPUT_FOLDER = 'finalCoverage'
const run = commands => {
  commands.forEach(command => execSync(command, { stdio: 'inherit' }))
}
// Create the intermediate folder and move the reports from cypress and jest inside it
fs.emptyDirSync(INTERMEDIATE_FOLDER)
const sourceFile = path.join(CYPRESS_COVERAGE_FOLDER, 'coverage-final.json');
const destinationFile = path.join(INTERMEDIATE_FOLDER, 'from-cypress.json');
if (!fs.existsSync(sourceFile)) {
  console.error(`Source file does not exist: ${sourceFile}`);
} else {
  // Check if the destination directory exists
  if (!fs.existsSync(INTERMEDIATE_FOLDER)) {
    console.log(`Destination directory does not exist. Creating: ${INTERMEDIATE_FOLDER}`);
    try {
      fs.mkdirSync(INTERMEDIATE_FOLDER, { recursive: true });
    } catch (err) {
      console.error(`Failed to create directory: ${err}`);
    }
  }
}
fs.copyFileSync(`${CYPRESS_COVERAGE_FOLDER}/coverage-final.json`, `${INTERMEDIATE_FOLDER}/from-cypress.json`)
fs.copyFileSync(`${JEST_COVERAGE_FOLDER}/coverage-final.json`, `${INTERMEDIATE_FOLDER}/from-jest.json`)
fs.emptyDirSync('.nyc_output')
fs.emptyDirSync(FINAL_OUTPUT_FOLDER)
// Run "nyc merge" inside the intermediate folder, merging the two coverage files into one,
// then generate the final report on the coverage folder
run([
  // "nyc merge" will create a "coverage.json" file on the root, we move it to .nyc_output
  `nyc merge ${INTERMEDIATE_FOLDER} && mv coverage.json .nyc_output/out.json`,
  `nyc report --reporter lcov --report-dir ${FINAL_OUTPUT_FOLDER}`
])

// Clean up
fs.rmdirSync(CYPRESS_COVERAGE_FOLDER, { recursive: true })
fs.rmdirSync(JEST_COVERAGE_FOLDER, { recursive: true })
fs.rmdirSync(INTERMEDIATE_FOLDER, { recursive: true })
