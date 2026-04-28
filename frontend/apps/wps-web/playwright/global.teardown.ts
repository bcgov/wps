import fs from 'node:fs'
import path from 'node:path'
import libCoverage from 'istanbul-lib-coverage'

const coverageTempDir = path.join(import.meta.dirname, '..', '.nyc_temp_playwright')
const outputDir = path.join(import.meta.dirname, '..', 'coverage-playwright')
const outputFile = path.join(outputDir, 'coverage-final.json')

export default function globalTeardown() {
  if (!fs.existsSync(coverageTempDir)) {
    console.log('No Playwright coverage data found — skipping merge.')
    return
  }

  const map = libCoverage.createCoverageMap()

  for (const file of fs.readdirSync(coverageTempDir)) {
    if (!file.endsWith('.json')) continue
    const raw = JSON.parse(fs.readFileSync(path.join(coverageTempDir, file), 'utf-8'))
    map.merge(raw)
  }

  fs.mkdirSync(outputDir, { recursive: true })
  fs.writeFileSync(outputFile, JSON.stringify(map.toJSON(), null, 2))

  // Clean up temp files
  fs.rmSync(coverageTempDir, { recursive: true, force: true })

  console.log(`Playwright coverage written to ${outputFile}`)
}
