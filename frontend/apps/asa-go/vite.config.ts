import { sentryVitePlugin } from "@sentry/vite-plugin";
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "node:path";
import { resolve } from "path";

const env = loadEnv(process.env.NODE_ENV ?? "development", process.cwd(), "");

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    sentryVitePlugin({
      org: "bcps-wps",
      project: "asago",
      authToken: env.SENTRY_AUTH_TOKEN,
    }),
  ],

  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
      app: resolve(__dirname, "src", "app"),
      utils: resolve(__dirname, "src", "utils"),
      api: resolve(__dirname, "src", "api"),
      "#root": resolve(__dirname),
    },
  },

  build: {
    sourcemap: true,
  },
});
