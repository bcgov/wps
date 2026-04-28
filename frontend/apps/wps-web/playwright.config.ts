import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './playwright',
  globalTeardown: './playwright/global.teardown',
  retries: 1,
  workers: 2,
  use: {
    baseURL: 'http://localhost:3030'
  },
  projects: [
    {
      name: 'chromium',
      use: { channel: 'chrome' }
    }
  ],
  webServer: {
    command: 'export $(cat .env.playwright | xargs) && yarn start',
    url: 'http://localhost:3030',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000
  }
})
