import path from 'node:path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path';
import svgr from "vite-plugin-svgr";
import istanbul from 'vite-plugin-istanbul';
import { sentryVitePlugin } from "@sentry/vite-plugin";

export default defineConfig({
  build: {
    sourcemap: true,
    outDir: 'build',
  },
  optimizeDeps: {
    include: ['@mui/material/Tooltip', '@emotion/styled/base', '@mui/material/Unstable_Grid2'],
  },
  plugins: [
    {
      name: 'build-html',
      apply: 'build',
      transformIndexHtml: (html) => {
        return {
          html,
          tags: [
            {
              tag: 'script',
              attrs: {
                src: '/config.js',
              },
              injectTo: 'head',
            },
          ],
        }
      },
    },
    react({
      jsxImportSource: "@emotion/react",
      babel: {
        plugins: ["@emotion/babel-plugin"],
      },
    }),
    , svgr(),
    istanbul({
      include: 'src/*',
      exclude: ['node_modules', 'test/'],
      extension: ['.js', '.ts'],
      cypress: true
    }),
    // sentryVitePlugin({
    //   org: "bcps-wps",
    //   project: "frontend",
    //   authToken: process.env.SENTRY_AUTH_TOKEN,
    //   sourcemaps: {
    //     filesToDeleteAfterUpload: ['**/*.map'],
    //   },
    // }),
  ],
  server: {
    port: Number(process.env.PORT) || 3000,
    watch: {
      ignored: [
        path.join(__dirname, 'coverage-cypress/**'),
        path.join(__dirname, 'cypress/**'),
        path.join(__dirname, 'finalCoverage/**'),
      ]
    },
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
  },

})

