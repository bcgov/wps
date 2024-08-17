import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path';
import svgr from "vite-plugin-svgr";
import istanbul from 'vite-plugin-istanbul';

export default () => {
  return defineConfig({
    plugins: [react(), svgr(),
    istanbul({
      include: 'src/*',
      exclude: ['node_modules', 'test/'],
      extension: ['.js', '.ts'],
      requireEnv: true,
    }),
    ],
    server: {
      port: 3030
    },
    resolve: {
      alias: {
        'app': resolve(__dirname, 'src', 'app'),
        'features': resolve(__dirname, 'src', 'features'),
        'utils': resolve(__dirname, 'src', 'utils'),
        'commonSlices': resolve(__dirname, 'src', 'commonSlices'),
        'components': resolve(__dirname, 'src', 'components'),
        'api': resolve(__dirname, 'src', 'api'),
        'documents': resolve(__dirname, 'src', 'documents'),
        '#root': resolve(__dirname)
      }
    }
  })
}

