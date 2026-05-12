// @vitest-environment node

import { beforeEach, describe, expect, it, vi } from "vitest";

describe("api axios client", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.resetModules();
  });

  it("returns the shared API client", async () => {
    const { api, getApiClient } = await import("@/api/axios");

    expect(getApiClient()).toBe(api);
  });
});
