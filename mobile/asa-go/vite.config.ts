import path, { resolve } from 'node:path'
import { sentryVitePlugin } from '@sentry/vite-plugin'
import react from '@vitejs/plugin-react-swc'
import { loadEnv } from 'vite'
import { defineConfig } from 'vitest/config'

const env = loadEnv(process.env.NODE_ENV ?? 'development', process.cwd(), '')

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    sentryVitePlugin({
      org: 'bcps-wps',
      project: 'asago',
      authToken: env.SENTRY_AUTH_TOKEN
    })
  ],

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      app: resolve(__dirname, 'src', 'app'),
      utils: resolve(__dirname, 'src', 'utils'),
      api: resolve(__dirname, 'src', 'api'),
      '#root': resolve(__dirname)
    }
  },

  build: {
    sourcemap: true
  },

  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/setupTests.ts'],
    server: {
      deps: {
        inline: ['react-transition-group', /@mui\//]
      }
    }
  }
})
