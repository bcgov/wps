/// <reference types="vitest" />
import { defineConfig, mergeConfig } from "vitest/config";
import viteConfig from "./vite.config";

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      coverage: {
        provider: "v8",
        reportsDirectory: "./coverage",
        include: ["src/**/*.{ts,tsx}", "!src/**/*.d.ts", "!src/index.tsx"],
      },
      include: ["src/**/*.{spec,test}.{js,jsx,ts,tsx}"],
      globals: true,
      environment: "jsdom",
      setupFiles: "src/setupTests.ts",
      // Define environment variables for testing
      env: {
        VITE_KEYCLOAK_REALM: "test-realm",
        VITE_KEYCLOAK_AUTH_URL: "https://auth.test.com",
        VITE_KEYCLOAK_CLIENT: "test-client",
      },
    },
  })
);
