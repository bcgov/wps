import path from 'node:path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'
import svgr from 'vite-plugin-svgr'
import istanbul from 'vite-plugin-istanbul'
import { sentryVitePlugin } from '@sentry/vite-plugin'

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
    alias: [
      // @wps/* package aliases
      { find: '@wps/api', replacement: resolve(__dirname, '../../packages/api/src') },
      { find: '@wps/utils', replacement: resolve(__dirname, '../../packages/utils/src') },
      { find: '@wps/types', replacement: resolve(__dirname, '../../packages/types/src') },
      { find: '@wps/ui', replacement: resolve(__dirname, '../../packages/ui/src') },
      // @/app/theme remapped to ui package (must come before @/app/ and @/)
      { find: '@/app/theme', replacement: resolve(__dirname, '../../packages/ui/src/theme') },
      // @/api, @/utils, @/components remapped to extracted packages
      { find: /^@\/api\/(.*)/, replacement: resolve(__dirname, '../../packages/api/src/$1') },
      { find: /^@\/utils\/(.*)/, replacement: resolve(__dirname, '../../packages/utils/src/$1') },
      { find: /^@\/components\/(.*)/, replacement: resolve(__dirname, '../../packages/ui/src/$1') },
      // bare aliases
      { find: '@', replacement: path.resolve(__dirname, './src') },
      // app/theme specifically remapped to ui package (must come before app)
      { find: 'app/theme', replacement: resolve(__dirname, '../../packages/ui/src/theme') },
      { find: 'app', replacement: resolve(__dirname, 'src/app') },
      { find: 'features', replacement: resolve(__dirname, 'src/features') },
      { find: 'utils', replacement: resolve(__dirname, '../../packages/utils/src') },
      { find: 'commonSlices', replacement: resolve(__dirname, 'src/commonSlices') },
      { find: 'components', replacement: resolve(__dirname, '../../packages/ui/src') },
      { find: 'api', replacement: resolve(__dirname, '../../packages/api/src') },
      { find: 'documents', replacement: resolve(__dirname, 'src/documents') },
      { find: '#root', replacement: resolve(__dirname) }
    ]
  }
})
