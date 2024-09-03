/// <reference types="vitest" />
import { defineConfig, mergeConfig } from 'vitest/config'
import viteConfig from './vite.config'

export default mergeConfig(viteConfig, defineConfig({
  test: {
    coverage: {
      provider: 'istanbul',
      reportsDirectory: './coverage/lcov-report',
      include: [
        "src/**/*.{ts,tsx}",
        "!src/**/*.d.ts",
        "!src/index.tsx",
        "!src/app/*.{ts,tsx}"
        // "src/api/moreCast2API.ts"
      ]

    },
    include: [
      "src/**/*.{spec,test}.{js,jsx,ts,tsx}",
    ],
    exclude: [
      "src/features/auth/slices/authenticationSlice.test.ts",
    ],
    globals: true,
    environment: 'jsdom',
    setupFiles: 'src/setupTests.ts'
  },
}))
