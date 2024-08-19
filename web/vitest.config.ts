/// <reference types="vitest" />
import { defineConfig, mergeConfig } from 'vitest/config'
import viteConfig from './vite.config'

export default mergeConfig(viteConfig, defineConfig({
  test: {
    coverage: {
      provider: 'istanbul',
      include: [
        "src/**/*.{ts,tsx}",
        "!src/**/*.d.ts",
        "!src/index.tsx",
        "!src/serviceWorker.ts",
        "!src/app/*.{ts,tsx}"
      ]
    },
    include: [
      "src/**/*.{spec,test}.{js,jsx,ts,tsx}",
      "**/features/fbaCalculator/components/fbaProgressRow.test.tsx"
    ],
    exclude: [
      "src/features/auth/slices/authenticationSlice.test.ts",
      "src/features/fba/components/map/fbaMap.test.tsx"
    ],
    globals: true,
    environment: 'jsdom',
    setupFiles: 'src/setupTests.ts'
  },
}))
