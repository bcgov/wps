import path from 'node:path'
import type { CoverageReportOptions } from 'monocart-coverage-reports'
import playwrightConfig from '../playwright.config'

const appDir = path.join(import.meta.dirname, '..')
// Coverage is recorded per script URL, so match scripts served by the dev server Playwright tests against
const devServer = new URL(playwrightConfig.use!.baseURL!).host

// Shared by the fixture (each worker adds V8 coverage to the cache) and the
// teardown (merges the cache into one Istanbul report for mergeCoverage.cjs).
export const coverageOptions: CoverageReportOptions = {
  name: 'Playwright coverage',
  outputDir: path.join(appDir, 'coverage-playwright'),
  reports: [['json', { file: 'coverage-final.json' }], 'console-summary'],
  // Only wps-web TypeScript modules served by the Vite dev server (not CSS or inline page scripts)
  entryFilter: entry => {
    const url = new URL(entry.url)
    return url.host === devServer && url.pathname.startsWith('/src/') && /\.tsx?$/.test(url.pathname)
  },
  // Vite source maps only name the bare file (e.g. "App.tsx"), so rebuild the path from the
  // served URL. Absolute paths match the keys in the Vitest coverage reports.
  sourcePath: (filePath, { distFile }) => {
    const servedPath = distFile?.split(`${devServer.replace(':', '-')}/`)[1]
    return servedPath ? path.resolve(appDir, servedPath) : filePath
  },
  sourceFilter: sourcePath => sourcePath.startsWith(path.join(appDir, 'src')),
  // Workers share the cache, so only global setup clears it
  cleanCache: false
}
