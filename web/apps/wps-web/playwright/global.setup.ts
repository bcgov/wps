import fs from 'node:fs'
import { coverageOptions } from './coverage-options'

export default function globalSetup() {
  // Remove coverage from previous runs before any worker writes to the cache
  fs.rmSync(coverageOptions.outputDir!, { recursive: true, force: true })
}
