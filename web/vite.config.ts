import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import istanbul from 'vite-plugin-istanbul'
import tsconfigPaths from 'vite-tsconfig-paths'

// https://vitejs.dev/config/
export default defineConfig({
  server: {
    port: 3030
  },
  plugins: [
    react(),
    tsconfigPaths(),
    istanbul({
      include: 'src/*',
      exclude: ['node_modules'],
      extension: ['.tsx', '.ts'],
      cypress: true,
      requireEnv: false
    })
  ]
})
