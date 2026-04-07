import { FireCentreInfo, getFireCentreInfo } from "@/api/fbaAPI";
import { createTestStore } from "@/testUtils";
import { FIRE_CENTRE_INFO_KEY, readFromFilesystem } from "@/utils/storage";
import { Preferences } from "@capacitor/preferences";
import { act } from "@testing-library/react";
import { DateTime } from "luxon";
import { beforeEach, describe, expect, it, Mock, vi } from "vitest";
import settingsSlice, {
  fetchFireCentreInfo,
  getFireCentreInfoFailed,
  getFireCentreInfoStart,
  getFireCentreInfoSuccess,
  initialState,
  initPinnedFireCentre,
  initSubscriptions,
  savePinnedFireCentre,
  saveSubscriptions,
  setPinnedFireCentre,
  setSubscriptions,
  SettingsState,
} from "./settingsSlice";

// Mock the @capacitor/preferences module
vi.mock("@capacitor/preferences", () => ({
  Preferences: {
    get: vi.fn(),
    set: vi.fn(),
    remove: vi.fn(),
  },
}));

// Mock the storage utilities
vi.mock("@/utils/storage", () => ({
  readFromFilesystem: vi.fn(),
  writeToFileSystem: vi.fn(),
  FIRE_CENTRE_INFO_CACHE_EXPIRATION: 24,
  FIRE_CENTRE_INFO_KEY: "fireCentreInfo",
}));

// Mock the API
vi.mock("@/api/fbaAPI", () => ({
  getFireCentreInfo: vi.fn(),
}));

describe("settingsSlice", () => {
  // Test data factories
  const createSettingsState = (
    overrides: Partial<SettingsState> = {},
  ): SettingsState => ({
    ...initialState,
    ...overrides,
  });

  const createFireCentreInfo = (
    overrides: Partial<FireCentreInfo> = {},
  ): FireCentreInfo => ({
    fire_centre_name: "Test Fire Centre",
    fire_zone_units: [{ id: 1, name: "Test Zone" }],
    ...overrides,
  });

  const expectSettingsState = (
    state: SettingsState,
    expected: Partial<SettingsState>,
  ) => {
    Object.entries(expected).forEach(([key, value]) => {
      if (Array.isArray(value)) {
        expect(state[key as keyof SettingsState]).toEqual(value);
      } else {
        expect(state[key as keyof SettingsState]).toBe(value);
      }
    });
  };

  describe("reducers", () => {
    it("should return the initial state", () => {
      expect(settingsSlice(undefined, { type: "unknown" })).toEqual(
        initialState,
      );
    });

    it("should handle getFireCentreInfoStart", () => {
      const previousState = createSettingsState({
        loading: false,
        error: "Previous error",
        fireCentreInfos: [
          { fire_centre_name: "Old Fire Centre", fire_zone_units: [] },
        ],
      });

      const nextState = settingsSlice(previousState, getFireCentreInfoStart());

      expectSettingsState(nextState, {
        loading: true,
        error: null,
        fireCentreInfos: [],
      });
    });

    it("should handle getFireCentreInfoFailed", () => {
      const previousState = createSettingsState({
        loading: true,
      });
      const errorMessage = "Failed to load fire centre info";

      const nextState = settingsSlice(
        previousState,
        getFireCentreInfoFailed(errorMessage),
      );

      expectSettingsState(nextState, {
        loading: false,
        error: errorMessage,
      });
    });

    it("should handle getFireCentreInfoSuccess", () => {
      const previousState = createSettingsState({
        loading: true,
        error: "Previous error",
      });
      const fireCentreInfos = [
        createFireCentreInfo({ fire_centre_name: "Fire Centre 1" }),
        createFireCentreInfo({ fire_centre_name: "Fire Centre 2" }),
      ];

      const nextState = settingsSlice(
        previousState,
        getFireCentreInfoSuccess(fireCentreInfos),
      );

      expectSettingsState(nextState, {
        loading: false,
        error: null,
        fireCentreInfos: fireCentreInfos,
      });
    });

    it("should handle setPinnedFireCentre", () => {
      const previousState = createSettingsState({
        pinnedFireCentre: null,
      });
      const fireCentre = "Kamloops";

      const nextState = settingsSlice(
        previousState,
        setPinnedFireCentre(fireCentre),
      );

      expectSettingsState(nextState, {
        pinnedFireCentre: fireCentre,
      });
    });

    it("should handle setPinnedFireCentre with null", () => {
      const previousState = createSettingsState({
        pinnedFireCentre: "Kamloops",
      });

      const nextState = settingsSlice(previousState, setPinnedFireCentre(null));

      expectSettingsState(nextState, {
        pinnedFireCentre: null,
      });
    });

    it("should handle setSubscriptions", () => {
      const previousState = createSettingsState({
        subscriptions: [],
      });
      const subscriptions = [1, 2, 3];

      const nextState = settingsSlice(
        previousState,
        setSubscriptions(subscriptions),
      );

      expectSettingsState(nextState, {
        subscriptions: subscriptions,
      });
    });

    it("should handle setSubscriptions with empty array", () => {
      const previousState = createSettingsState({
        subscriptions: [1, 2, 3],
      });

      const nextState = settingsSlice(previousState, setSubscriptions([]));

      expectSettingsState(nextState, {
        subscriptions: [],
      });
    });
  });

  describe("thunks", () => {
    beforeEach(() => {
      vi.resetAllMocks();
    });

    describe("initPinnedFireCentre", () => {
      it("should dispatch setPinnedFireCentre when stored value exists", async () => {
        const store = createTestStore();
        (Preferences.get as Mock).mockResolvedValue({
          value: "Kamloops",
        });

        await store.dispatch(initPinnedFireCentre());

        expectSettingsState(store.getState().settings, {
          pinnedFireCentre: "Kamloops",
        });
      });

      it("should not dispatch setPinnedFireCentre when no stored value", async () => {
        const store = createTestStore();
        (Preferences.get as Mock).mockResolvedValue({ value: null });

        act(async () => {
          store.dispatch(initPinnedFireCentre());
        });

        expectSettingsState(store.getState().settings, {
          pinnedFireCentre: null,
        });
      });
    });

    describe("initSubscriptions", () => {
      it("should dispatch setSubscriptions when stored value exists", async () => {
        const store = createTestStore();
        (Preferences.get as Mock).mockResolvedValue({
          value: JSON.stringify([1, 2, 3]),
        });

        await store.dispatch(initSubscriptions());

        expectSettingsState(store.getState().settings, {
          subscriptions: [1, 2, 3],
        });
      });

      it("should not dispatch setSubscriptions when no stored value", async () => {
        const store = createTestStore();
        (Preferences.get as Mock).mockResolvedValue({ value: null });

        await store.dispatch(initSubscriptions());

        expectSettingsState(store.getState().settings, {
          subscriptions: [],
        });
      });

      it("should handle invalid JSON gracefully", async () => {
        const store = createTestStore();
        const consoleSpy = vi
          .spyOn(console, "error")
          .mockImplementation(() => {});
        (Preferences.get as Mock).mockResolvedValue({
          value: "invalid-json",
        });

        await store.dispatch(initSubscriptions());

        expectSettingsState(store.getState().settings, {
          subscriptions: [],
        });
        expect(consoleSpy).toHaveBeenCalled();
        consoleSpy.mockRestore();
      });
    });

    describe("saveSubscriptions", () => {
      it("should save subscriptions to preferences and update state", async () => {
        const store = createTestStore();
        (Preferences.set as Mock).mockResolvedValue(undefined);

        await store.dispatch(saveSubscriptions([1, 2, 3]));

        expect(Preferences.set).toHaveBeenCalledWith({
          key: "asaGoSubscriptions",
          value: "[1,2,3]",
        });
        expectSettingsState(store.getState().settings, {
          subscriptions: [1, 2, 3],
        });
      });

      it("should save empty subscriptions array", async () => {
        const store = createTestStore();
        (Preferences.set as Mock).mockResolvedValue(undefined);

        await store.dispatch(saveSubscriptions([]));

        expect(Preferences.set).toHaveBeenCalledWith({
          key: "asaGoSubscriptions",
          value: "[]",
        });
        expectSettingsState(store.getState().settings, {
          subscriptions: [],
        });
      });
    });

    describe("savePinnedFireCentre", () => {
      it("should save fire centre to preferences and update state", async () => {
        const store = createTestStore();
        (Preferences.set as Mock).mockResolvedValue(undefined);

        await store.dispatch(savePinnedFireCentre("Kamloops"));

        expect(Preferences.set).toHaveBeenCalledWith({
          key: "asaGoPinnedFireCentre",
          value: "Kamloops",
        });
        expectSettingsState(store.getState().settings, {
          pinnedFireCentre: "Kamloops",
        });
      });

      it("should remove fire centre from preferences when null", async () => {
        const store = createTestStore();
        (Preferences.remove as Mock).mockResolvedValue(undefined);

        await store.dispatch(savePinnedFireCentre(null));

        expect(Preferences.remove).toHaveBeenCalledWith({
          key: "asaGoPinnedFireCentre",
        });
        expectSettingsState(store.getState().settings, {
          pinnedFireCentre: null,
        });
      });
    });
    describe("fetchFireCentreInfo", () => {
      beforeEach(() => {
        // Reset all mocks before each test
        vi.clearAllMocks();
      });

      const today = DateTime.now().toISO();
      const yesterday = DateTime.now().plus({ days: -2 }).toISO();

      const mockFireCentreInfoA: FireCentreInfo = {
        fire_centre_name: "Kamloops Fire Centre",
        fire_zone_units: [
          {
            id: 1,
            name: "Vernon Fire Zone",
          },
        ],
      };
      const mockFireCentreInfoB: FireCentreInfo = {
        fire_centre_name: "Cariboo Fire Centre",
        fire_zone_units: [
          {
            id: 2,
            name: "Chilcoltin Fire Zone",
          },
        ],
      };

      const mockCacheWithNoData = () => {
        (readFromFilesystem as Mock).mockImplementation(() => {
          return null;
        });
      };
      const mockCacheWithData = (isStale: boolean) => {
        (readFromFilesystem as Mock).mockImplementation((_filesystem, key) => {
          if (key === FIRE_CENTRE_INFO_KEY) {
            return {
              lastUpdated: isStale ? yesterday : today,
              data: isStale ? [mockFireCentreInfoA] : [mockFireCentreInfoB],
            };
          } else {
            return null;
          }
        });
      };

      it("should call API and dispatch success when cache is empty and app online", async () => {
        mockCacheWithNoData(); // mock cache returns null
        (getFireCentreInfo as Mock).mockResolvedValue({
          fire_centre_info: [mockFireCentreInfoA],
        });
        const store = createTestStore({
          settings: { ...initialState },
          networkStatus: {
            networkStatus: { connected: true, connectionType: "wifi" },
          },
        });
        await store.dispatch(fetchFireCentreInfo());
        const state = store.getState().settings;
        expect(state.fireCentreInfos).toEqual([mockFireCentreInfoA]);
        expect(state.loading).toBe(false);
        expect(getFireCentreInfo).toHaveBeenCalledOnce();
      });

      it("should call API and dispatch success when cache is stale and app online", async () => {
        mockCacheWithData(true); // mock cache returns mockFireCentreA
        (getFireCentreInfo as Mock).mockResolvedValue({
          fire_centre_info: [mockFireCentreInfoB],
        }); // API call returns mockFireCentreB
        const store = createTestStore({
          settings: { ...initialState },
          networkStatus: {
            networkStatus: { connected: true, connectionType: "wifi" },
          },
        });
        await store.dispatch(fetchFireCentreInfo());
        const state = store.getState().settings;
        expect(state.fireCentreInfos).toEqual([mockFireCentreInfoB]);
        expect(state.loading).toBe(false);
        expect(getFireCentreInfo).toHaveBeenCalledOnce();
      });

      it("should not call API when cache is fresh and app online", async () => {
        mockCacheWithData(false); // mock cache returns mockFireCentreInfoB
        const store = createTestStore({
          settings: { ...initialState },
          networkStatus: {
            networkStatus: { connected: true, connectionType: "wifi" },
          },
        });
        await store.dispatch(fetchFireCentreInfo());
        const state = store.getState().settings;
        expect(state.fireCentreInfos).toEqual([mockFireCentreInfoB]);
        expect(state.loading).toBe(false);
        expect(getFireCentreInfo).not.toBeCalled();
      });

      it("should dispatch error when cache is empty and app is offline", async () => {
        mockCacheWithNoData();
        const store = createTestStore({
          settings: { ...initialState },
          networkStatus: {
            networkStatus: { connected: false, connectionType: "none" },
          },
        });
        await store.dispatch(fetchFireCentreInfo());
        const state = store.getState().settings;
        expect(state.loading).toBe(false);
        expect(state.error).toMatch(/Unable to refresh fire centre info data/);
      });

      it("should dispatch success when cache is stale and app is offline", async () => {
        mockCacheWithData(true);
        const store = createTestStore({
          settings: { ...initialState },
          networkStatus: {
            networkStatus: { connected: false, connectionType: "none" },
          },
        });
        await store.dispatch(fetchFireCentreInfo());
        const state = store.getState().settings;
        expect(state.loading).toBe(false);
        expect(state.fireCentreInfos).toEqual([mockFireCentreInfoA]);
      });
    });
  });
});
