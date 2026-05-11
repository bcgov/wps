// @vitest-environment node

import { beforeEach, describe, expect, it, vi } from "vitest";

const loadAxiosApi = async () => {
  vi.doMock("@/utils/env", () => ({
    API_BASE_URL: "https://psu-api.example.com/api",
    API_PUBLIC_BASE_URL: "https://public-psu-api.example.com/api",
  }));

  return import("@/api/axios");
};

describe("api axios client mode", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.resetModules();
  });

  it("uses the public API client by default", async () => {
    const { getApiClient, publicApi } = await loadAxiosApi();

    expect(getApiClient()).toBe(publicApi);
  });

  it("uses the authenticated API client in authenticated mode", async () => {
    const { authenticatedApi, getApiClient, setApiMode } = await loadAxiosApi();

    setApiMode("authenticated");

    expect(getApiClient()).toBe(authenticatedApi);
  });

  it("can switch back to the public API client", async () => {
    const { getApiClient, publicApi, setApiMode } = await loadAxiosApi();

    setApiMode("authenticated");
    setApiMode("public");

    expect(getApiClient()).toBe(publicApi);
  });

  it("configures the expected base URLs", async () => {
    const { authenticatedApi, publicApi } = await loadAxiosApi();

    expect(authenticatedApi.defaults.baseURL).toBe(
      "https://psu-api.example.com/api",
    );
    expect(publicApi.defaults.baseURL).toBe(
      "https://public-psu-api.example.com/api/asa-go",
    );
  });
});
