import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useDeviceId } from "./useDeviceId";

vi.mock("@capacitor/device", () => ({
  Device: { getId: vi.fn() },
}));

import { Device } from "@capacitor/device";

describe("useDeviceId", () => {
  beforeEach(() => {
    vi.mocked(Device.getId).mockResolvedValue({ identifier: "test-device-id" });
  });

  it("returns null before Device.getId resolves", () => {
    vi.mocked(Device.getId).mockReturnValue(new Promise(() => {}));
    const { result } = renderHook(() => useDeviceId());
    expect(result.current).toBeNull();
  });

  it("returns the device identifier after resolving", async () => {
    const { result } = renderHook(() => useDeviceId());
    await act(async () => {});
    expect(result.current).toBe("test-device-id");
  });

  it("returns null and logs an error when Device.getId fails", async () => {
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    vi.mocked(Device.getId).mockRejectedValue(new Error("hardware error"));
    const { result } = renderHook(() => useDeviceId());
    await act(async () => {});
    expect(result.current).toBeNull();
    expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining("Failed to get device ID"));
    consoleSpy.mockRestore();
  });
});
