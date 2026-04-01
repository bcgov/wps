import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "node:path";
import { resolve } from "path";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
      app: resolve(__dirname, "src", "app"),
      utils: resolve(__dirname, "src", "utils"),
      api: resolve(__dirname, "src", "api"),
      "#root": resolve(__dirname),
    },
  },
});
