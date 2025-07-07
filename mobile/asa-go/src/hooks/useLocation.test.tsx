import { renderHook } from "@testing-library/react";
import { Provider } from "react-redux";
import { Geolocation } from "@capacitor/geolocation";
import { vi, describe, it, expect, Mock } from "vitest";
import { createTestStore } from "@/testUtils";
import { useLocation } from "@/hooks/useLocation";
import { App } from "@capacitor/app";

// Spy/mocks
vi.mock("@capacitor/app", () => ({
  App: {
    addListener: vi.fn(() =>
      Promise.resolve({
        remove: vi.fn(),
      })
    ),
  },
}));

vi.mock("@capacitor/geolocation", () => ({
  Geolocation: {
    checkPermissions: vi.fn(),
    requestPermissions: vi.fn(),
    getCurrentPosition: vi.fn(),
    watchPosition: vi.fn(),
    clearWatch: vi.fn(),
  },
}));

describe("useLocation", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    (Geolocation.checkPermissions as Mock).mockResolvedValue({
      location: "granted",
    });
    (Geolocation.requestPermissions as Mock).mockResolvedValue({
      location: "granted",
    });

    (Geolocation.getCurrentPosition as Mock).mockResolvedValue({
      coords: { latitude: 0, longitude: 0, accuracy: 10 },
      timestamp: Date.now(),
    });

    (Geolocation.watchPosition as Mock).mockImplementation(
      (_opts, callback) => {
        callback(
          {
            coords: { latitude: 1, longitude: 2, accuracy: 15 },
            timestamp: Date.now(),
          },
          null
        );
        return Promise.resolve("mock-id");
      }
    );
  });

  it("dispatches location updates", async () => {
    const store = createTestStore({
      geolocation: {
        position: null,
        error: null,
        loading: false,
      },
    });

    renderHook(() => useLocation({ enabled: true }), {
      wrapper: ({ children }) => <Provider store={store}>{children}</Provider>,
    });

    await new Promise((resolve) => setTimeout(resolve, 100));

    const state = store.getState().geolocation;

    expect(state.position?.coords.latitude).toBe(1);
    expect(state.error).toBeNull();
    expect(Geolocation.getCurrentPosition).toHaveBeenCalled();
    expect(Geolocation.watchPosition).toHaveBeenCalled();
  });

  it("dispatches error if permission denied", async () => {
    (Geolocation.checkPermissions as Mock).mockResolvedValueOnce({
      location: "denied",
    });
    (Geolocation.requestPermissions as Mock).mockResolvedValueOnce({
      location: "denied",
    });

    const store = createTestStore();

    renderHook(() => useLocation({ enabled: true }), {
      wrapper: ({ children }) => <Provider store={store}>{children}</Provider>,
    });

    await new Promise((resolve) => setTimeout(resolve, 100));

    const state = store.getState().geolocation;

    expect(state.error).toBe("Location permission denied");
  });

  it("starts and stops watching based on app state changes", async () => {
    const removeMock = vi.fn();
    let appStateCallback: ((state: { isActive: boolean }) => void) | undefined;

    // Override the mock implementation for this test
    (App.addListener as Mock).mockImplementation((_event, callback) => {
      appStateCallback = callback;
      return Promise.resolve({ remove: removeMock });
    });

    const store = createTestStore();

    renderHook(() => useLocation({ enabled: true }), {
      wrapper: ({ children }) => <Provider store={store}>{children}</Provider>,
    });

    await new Promise((r) => setTimeout(r, 50));
    expect(Geolocation.watchPosition).toHaveBeenCalledTimes(1);

    // Simulate backgrounding
    appStateCallback?.({ isActive: false });
    await new Promise((r) => setTimeout(r, 10));
    expect(Geolocation.clearWatch).toHaveBeenCalled();

    // Simulate foregrounding
    appStateCallback?.({ isActive: true });
    await new Promise((r) => setTimeout(r, 10));
    expect(Geolocation.watchPosition).toHaveBeenCalledTimes(2);
  });
});
