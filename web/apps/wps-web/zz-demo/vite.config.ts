// Demo only: serves the Insights page with a mocked API. Run from apps/wps-web:
//   ../../node_modules/.bin/vite --config zz-demo/vite.config.ts
import path from 'node:path'
import react from '@vitejs/plugin-react-swc'
import { defineConfig } from 'vite'

const app = path.resolve(import.meta.dirname, '..')

export default defineConfig({
  root: import.meta.dirname,
  // Your local .env supplies the base map's URLs.
  envDir: app,
  plugins: [react({ plugins: [['@swc/plugin-emotion', {}]] })],
  server: { port: 5199, strictPort: true, host: '127.0.0.1', fs: { allow: [path.resolve(app, '../..')] } },
  optimizeDeps: { include: ['@mui/material/Tooltip', '@emotion/styled/base', '@mui/material/Grid'] },
  resolve: {
    extensions: ['.ts', '.tsx', '.js', '.jsx', '.json'],
    alias: [
      { find: /^@wps\/api(.*)/, replacement: path.resolve(app, '../../packages/api/src$1') },
      { find: /^@wps\/ui(.*)/, replacement: path.resolve(app, '../../packages/ui/src$1') },
      { find: /^@wps\/utils(.*)/, replacement: path.resolve(app, '../../packages/utils/src$1') },
      { find: '@', replacement: path.resolve(app, 'src') },
      { find: 'app', replacement: path.resolve(app, 'src/app') },
      { find: 'features', replacement: path.resolve(app, 'src/features') },
      { find: 'commonSlices', replacement: path.resolve(app, 'src/commonSlices') },
      { find: 'documents', replacement: path.resolve(app, 'src/documents') },
      { find: '#root', replacement: app }
    ]
  }
})
