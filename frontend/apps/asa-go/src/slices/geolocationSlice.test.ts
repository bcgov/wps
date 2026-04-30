import geolocationSlice, {
  geolocationInitialState,
  setError,
  setPosition,
  startWatchingLocation,
} from "@/slices/geolocationSlice";
import { vi, Mock } from "vitest";
import { Geolocation, Position } from "@capacitor/geolocation";
import { createTestStore } from "@/testUtils";

describe("geolocationSlice", () => {
  it("should handle setPosition", () => {
    const position = {
      coords: { latitude: 1, longitude: 2, accuracy: 10 },
      timestamp: 123456789,
    } as Position;

    const nextState = geolocationSlice(
      geolocationInitialState,
      setPosition(position)
    );
    expect(nextState.position).toEqual(position);
    expect(nextState.error).toBeNull();
  });

  it("should handle setError", () => {
    const error = "Permission denied";
    const nextState = geolocationSlice(
      geolocationInitialState,
      setError(error)
    );
    expect(nextState.error).toEqual(error);
    expect(nextState.position).toBeNull();
  });
});

describe("geolocationSlice thunks", () => {
  vi.mock("@capacitor/geolocation", () => ({
    Geolocation: {
      checkPermissions: vi.fn(),
      requestPermissions: vi.fn(),
      getCurrentPosition: vi.fn(),
      watchPosition: vi.fn(),
      clearWatch: vi.fn(),
    },
  }));

  beforeEach(() => {
    vi.resetAllMocks();
  });

  describe("startWatchingLocation", () => {
    const store = createTestStore();

    const setupGeolocationMocks = () => {
      (Geolocation.checkPermissions as Mock).mockResolvedValue({
        location: "granted",
      });
      (Geolocation.clearWatch as Mock).mockResolvedValue(null);
    };

    it("sets error state if permission is denied", async () => {
      (Geolocation.checkPermissions as Mock).mockResolvedValue({
        location: "denied",
      });
      (Geolocation.requestPermissions as Mock).mockResolvedValue({
        location: "denied",
      });

      await store.dispatch(startWatchingLocation());

      const state = store.getState().geolocation;
      expect(state.error).toBe("Location permission denied");
    });

    it("updates position state on position update", async () => {
      setupGeolocationMocks();
      let callback: (
        pos?: Position,
        err?: { message: string }
      ) => void = () => {};

      (Geolocation.watchPosition as Mock).mockImplementation((_opts, cb) => {
        callback = cb;
        return Promise.resolve("watch-id");
      });

      await store.dispatch(startWatchingLocation());

      const position = {
        coords: { latitude: 1, longitude: 2, accuracy: 10 },
        timestamp: 123456789,
      } as Position;

      callback(position, undefined);

      const state = store.getState().geolocation;
      expect(state.position).toEqual(position);
      expect(state.error).toBeNull();
    });

    it("sets error state on watch error", async () => {
      setupGeolocationMocks();
      let callback: (
        pos?: Position,
        err?: { message: string }
      ) => void = () => {};
      (Geolocation.watchPosition as Mock).mockImplementation((_opts, cb) => {
        callback = cb;
        return Promise.resolve("watch-id");
      });

      await store.dispatch(startWatchingLocation());

      callback(undefined, { message: "Some error" });

      const state = store.getState().geolocation;
      expect(state.error).toBe("Some error");
    });
  });
});
