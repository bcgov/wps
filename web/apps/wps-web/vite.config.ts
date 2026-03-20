import path from 'node:path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'
import svgr from 'vite-plugin-svgr'
import istanbul from 'vite-plugin-istanbul'
import { sentryVitePlugin } from '@sentry/vite-plugin'

const isProduction = process.env.NODE_ENV === 'production'

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
      include: ['src/**/*'],
      exclude: ['node_modules', 'test/'],
      extension: ['.js', '.ts', '.tsx'],
      cypress: true
    })
  ],
  server: {
    port: Number(process.env.PORT) || 3000,
    warmup: {
      clientFiles: ['./src/index.tsx', './src/app/App.tsx', './src/app/Routes.tsx']
    },
    watch: {
      ignored: [
        path.join(__dirname, 'coverage-cypress/**'),
        path.join(__dirname, 'cypress/**'),
        path.join(__dirname, 'finalCoverage/**')
      ]
    }
  },
  resolve: {
    extensions: ['.ts', '.tsx', '.js', '.jsx', '.json'],
    alias: [
      // In dev, resolve @wps/* packages from source for HMR support
      ...(!isProduction
        ? [
            { find: /^@wps\/api(.*)/, replacement: path.resolve(__dirname, '../../packages/api/src$1') },
            { find: /^@wps\/ui(.*)/, replacement: path.resolve(__dirname, '../../packages/ui/src$1') },
            { find: /^@wps\/utils(.*)/, replacement: path.resolve(__dirname, '../../packages/utils/src$1') }
          ]
        : []),
      // app-internal aliases
      { find: '@', replacement: path.resolve(__dirname, './src') },
      { find: 'app', replacement: resolve(__dirname, 'src/app') },
      { find: 'features', replacement: resolve(__dirname, 'src/features') },
      { find: 'commonSlices', replacement: resolve(__dirname, 'src/commonSlices') },
      { find: 'documents', replacement: resolve(__dirname, 'src/documents') },
      { find: '#root', replacement: resolve(__dirname) }
    ]
  }
})
