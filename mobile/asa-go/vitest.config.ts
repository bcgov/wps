/// <reference types="vitest" />
import { defineConfig, mergeConfig } from "vitest/config";
import viteConfig from "./vite.config";

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      coverage: {
        provider: "istanbul",
        reportsDirectory: "./coverage",
        include: ["src/**/*.{ts,tsx}", "!src/**/*.d.ts", "!src/index.tsx"],
      },
      include: ["src/**/*.{spec,test}.{js,jsx,ts,tsx}"],
      globals: true,
      environment: "jsdom",
      setupFiles: 'src/setupTests.ts'
    },
  })
);
