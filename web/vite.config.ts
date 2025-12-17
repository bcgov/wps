import path from 'node:path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'
import svgr from 'vite-plugin-svgr'
import istanbul from 'vite-plugin-istanbul'
import { sentryVitePlugin } from '@sentry/vite-plugin'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  build: {
    sourcemap: true,
    outDir: 'build'
  },
  //this is added to avoid error styled_default is not a function read more: https://github.com/vitejs/vite/issues/12423
  optimizeDeps: {
    include: ['@mui/material/Tooltip', '@emotion/styled/base', '@mui/material/Unstable_Grid2']
  },
  plugins: [
    {
      name: 'build-html',
      apply: 'build',
      transformIndexHtml(html) {
        return html.replace(
          /<meta name="viewport" content="width=device-width, initial-scale=1.0">/,
          `<meta name="viewport" content="width=device-width, initial-scale=1.0">
         <script src="config.js"></script>
    <script type="text/javascript">
      window.env = config
    </script>
        `
        )
      }
    },
    react({
      jsxImportSource: '@emotion/react',
      babel: {
        plugins: ['@emotion/babel-plugin']
      }
    }),
    svgr(),
    sentryVitePlugin({
      org: 'bcps-wps',
      project: 'frontend',
      authToken: process.env.SENTRY_AUTH_TOKEN,
      sourcemaps: {
        filesToDeleteAfterUpload: 'build/assets/**.map'
      }
    }),
    istanbul({
      include: 'src/*',
      exclude: ['node_modules', 'test/'],
      extension: ['.js', '.ts', '.tsx'],
      cypress: true
    }),
    VitePWA({
      registerType: 'prompt',
      injectRegister: false,
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff,woff2}'],
        cleanupOutdatedCaches: true,
        clientsClaim: true,
        maximumFileSizeToCacheInBytes: 3 * 1024 * 1024 // 3 MB limit
      },
      manifest: false,
      devOptions: {
        enabled: false
      }
    })
  ],
  server: {
    port: Number(process.env.PORT) || 3000,
    watch: {
      ignored: [
        path.join(__dirname, 'coverage-cypress/**'),
        path.join(__dirname, 'cypress/**'),
        path.join(__dirname, 'finalCoverage/**')
      ]
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      app: resolve(__dirname, 'src', 'app'),
      features: resolve(__dirname, 'src', 'features'),
      utils: resolve(__dirname, 'src', 'utils'),
      commonSlices: resolve(__dirname, 'src', 'commonSlices'),
      components: resolve(__dirname, 'src', 'components'),
      api: resolve(__dirname, 'src', 'api'),
      documents: resolve(__dirname, 'src', 'documents'),
      '#root': resolve(__dirname)
    }
  }
})
