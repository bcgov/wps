import { vi, describe, it, expect, beforeEach, Mock } from "vitest";
import settingsSlice, {
  initialState,
  SettingsState,
  getFireCenterInfoStart,
  getFireCenterInfoFailed,
  getFireCenterInfoSuccess,
  setPinnedFireCentre,
  setSubscriptions,
  initPinnedFireCentre,
  initSubscriptions,
  saveSubscriptions,
  savePinnedFireCentre,
} from "./settingsSlice";
import { createTestStore } from "@/testUtils";
import { FireCentreInfo } from "@/api/fbaAPI";

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
  FIRE_CENTER_INFO_CACHE_EXPIRATION: 24,
  FIRE_CENTER_INFO_KEY: "fire_centre_info",
}));

// Mock the API
vi.mock("@/api/fbaAPI", () => ({
  getFireCentreInfo: vi.fn(),
}));

// Mock dataSliceUtils
vi.mock("@/utils/dataSliceUtils", () => ({
  today: "2024-01-15",
}));

import { Preferences } from "@capacitor/preferences";
import { act } from "@testing-library/react";

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

    it("should handle getFireCenterInfoStart", () => {
      const previousState = createSettingsState({
        loading: false,
        error: "Previous error",
        fireCentreInfos: [
          { fire_centre_name: "Old Fire Centre", fire_zone_units: [] },
        ],
      });

      const nextState = settingsSlice(previousState, getFireCenterInfoStart());

      expectSettingsState(nextState, {
        loading: true,
        error: null,
        fireCentreInfos: [],
      });
    });

    it("should handle getFireCenterInfoFailed", () => {
      const previousState = createSettingsState({
        loading: true,
      });
      const errorMessage = "Failed to load fire centre info";

      const nextState = settingsSlice(
        previousState,
        getFireCenterInfoFailed(errorMessage),
      );

      expectSettingsState(nextState, {
        loading: false,
        error: errorMessage,
      });
    });

    it("should handle getFireCenterInfoSuccess", () => {
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
        getFireCenterInfoSuccess(fireCentreInfos),
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
  });
});
