import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react-swc'
import istanbul from 'vite-plugin-istanbul'
import tsconfigPaths from 'vite-tsconfig-paths'

const cypress = process.env.CYPRESS

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  if (cypress) {
    process.env = Object.assign(process.env, loadEnv(mode, process.cwd(), '.env.cypress'))
  }
  console.log(`Has cypress set: ${cypress}`)
  return {
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
        requireEnv: true,
        cypress: true
      })
    ]
  }
})
