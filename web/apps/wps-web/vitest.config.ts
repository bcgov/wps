/// <reference types="vitest" />
import { defineConfig, mergeConfig } from 'vitest/config'
import viteConfig from './vite.config'

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      server: {
        deps: {
          inline: ['react-transition-group', /@mui\//]
        }
      },
      coverage: {
        provider: 'v8',
        reportsDirectory: './coverage',
        include: ['src/**/*.{ts,tsx}', '!src/**/*.d.ts', '!src/index.tsx', '!src/app/*.{ts,tsx}']
      },
      include: ['src/**/*.{spec,test}.{js,jsx,ts,tsx}'],
      exclude: ['src/features/auth/slices/authenticationSlice.test.ts', 'src/test/testUtils.ts'],
      globals: true,
      environment: 'jsdom',
      setupFiles: ['src/setupTests.ts']
    }
  })
)
