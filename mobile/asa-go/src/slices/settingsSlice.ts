import { AppThunk } from "@/store";
import { today } from "@/utils/dataSliceUtils";
import {
  FIRE_CENTRE_INFO_CACHE_EXPIRATION,
  FIRE_CENTRE_INFO_KEY,
  readFromFilesystem,
  writeToFileSystem,
} from "@/utils/storage";
import { FirebaseMessaging } from "@capacitor-firebase/messaging";
import { PermissionState } from "@capacitor/core";
import { Filesystem } from "@capacitor/filesystem";
import { Preferences } from "@capacitor/preferences";
import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { FireCentreInfo, getFireCentreInfo } from "api/fbaAPI";
import { isNil, isNull } from "lodash";
import { DateTime } from "luxon";

export interface SettingsState {
  loading: boolean;
  error: string | null;
  fireCentreInfos: FireCentreInfo[];
  pinnedFireCentre: string | null;
  pushNotificationPermission: PermissionState | "unknown";
  subscriptions: number[];
}

export const initialState: SettingsState = {
  loading: false,
  error: null,
  fireCentreInfos: [],
  pinnedFireCentre: null,
  pushNotificationPermission: "unknown",
  subscriptions: [],
};

const PINNED_FIRE_CENTRE_KEY = "asaGoPinnedFireCentre";
const SUBSCRIPTIONS_KEY = "asaGoSubscriptions";

const settingsSlice = createSlice({
  name: "settings",
  initialState,
  reducers: {
    getFireCentreInfoStart(state: SettingsState) {
      state.error = null;
      state.loading = true;
      state.fireCentreInfos = [];
    },
    getFireCentreInfoFailed(
      state: SettingsState,
      action: PayloadAction<string>,
    ) {
      state.error = action.payload;
      state.loading = false;
    },
    getFireCentreInfoSuccess(
      state: SettingsState,
      action: PayloadAction<FireCentreInfo[]>,
    ) {
      state.error = null;
      state.fireCentreInfos = action.payload;
      state.loading = false;
    },
    setPinnedFireCentre(
      state: SettingsState,
      action: PayloadAction<string | null>,
    ) {
      state.pinnedFireCentre = action.payload;
    },
    setPushNotificationPermission(
      state: SettingsState,
      action: PayloadAction<PermissionState | "unknown">,
    ) {
      state.pushNotificationPermission = action.payload;
    },
    setSubscriptions(state: SettingsState, action: PayloadAction<number[]>) {
      state.subscriptions = action.payload;
    },
  },
});

export const {
  getFireCentreInfoStart,
  getFireCentreInfoFailed,
  getFireCentreInfoSuccess,
  setPinnedFireCentre,
  setPushNotificationPermission,
  setSubscriptions,
} = settingsSlice.actions;

export default settingsSlice.reducer;

export const initPinnedFireCentre = (): AppThunk => async (dispatch) => {
  // Read the pinned fire centre from @capacitor/preferences and store in redux state if it exists.
  const pinnedFireCentre = await Preferences.get({
    key: PINNED_FIRE_CENTRE_KEY,
  });
  if (!isNil(pinnedFireCentre?.value)) {
    dispatch(setPinnedFireCentre(pinnedFireCentre.value));
  }
};

export const initSubscriptions = (): AppThunk => async (dispatch) => {
  const result = await Preferences.get({
    key: SUBSCRIPTIONS_KEY,
  });
  try {
    if (result.value) {
      const subs = JSON.parse(result.value);
      if (subs && Array.isArray(subs)) {
        dispatch(setSubscriptions(subs));
      }
    }
  } catch (e) {
    console.error(
      `An error occurred when populating notification subscriptions: ${e}`,
    );
  }
};

export const saveSubscriptions =
  (subs: number[]): AppThunk =>
  async (dispatch) => {
    await Preferences.set({
      key: SUBSCRIPTIONS_KEY,
      value: JSON.stringify(subs),
    });
    dispatch(setSubscriptions(subs));
  };

export const getUpdatedSubscriptions = (
  subscriptions: number[],
  fireZoneUnitId: number,
) => {
  if (subscriptions.includes(fireZoneUnitId)) {
    return subscriptions.filter((sub) => sub !== fireZoneUnitId);
  }

  return [...subscriptions, fireZoneUnitId];
};

export const toggleSubscription =
  (fireZoneUnitId: number): AppThunk =>
  async (dispatch, getState) => {
    const { subscriptions } = getState().settings;
    dispatch(
      saveSubscriptions(getUpdatedSubscriptions(subscriptions, fireZoneUnitId)),
    );
  };

// Update @capacitor/preferences and redux state with pinned fire centre
export const savePinnedFireCentre =
  (fireCentre: string | null): AppThunk =>
  async (dispatch) => {
    if (isNull(fireCentre)) {
      await Preferences.remove({ key: PINNED_FIRE_CENTRE_KEY });
    } else {
      await Preferences.set({
        key: PINNED_FIRE_CENTRE_KEY,
        value: fireCentre,
      });
    }
    dispatch(setPinnedFireCentre(fireCentre));
  };

export const fetchFireCentreInfo =
  (): AppThunk => async (dispatch, getState) => {
    // Check for cached fire centers data. If the data is not stale save it in redux state.
    const cachedFireCentreInfo = await readFromFilesystem(
      Filesystem,
      FIRE_CENTRE_INFO_KEY,
    );
    const networkStatus = getState().networkStatus;
    if (!isNull(cachedFireCentreInfo)) {
      const lastUpdated = DateTime.fromISO(cachedFireCentreInfo.lastUpdated);
      // Update state from the cached data if it isn't stale or if we're offline.
      if (
        lastUpdated.plus({ hours: FIRE_CENTRE_INFO_CACHE_EXPIRATION }) >
          today ||
        !networkStatus.networkStatus.connected
      ) {
        dispatch(
          getFireCentreInfoSuccess(
            cachedFireCentreInfo.data as FireCentreInfo[],
          ),
        );
        return;
      }
    }
    // Cached data is not available or is stale so we need to fetch and cache if we're online.
    if (networkStatus.networkStatus.connected) {
      try {
        dispatch(getFireCentreInfoStart());
        const fireCentreInfo = await getFireCentreInfo();
        await writeToFileSystem(
          Filesystem,
          FIRE_CENTRE_INFO_KEY,
          fireCentreInfo.fire_centre_info,
          today,
        );
        dispatch(getFireCentreInfoSuccess(fireCentreInfo.fire_centre_info));
      } catch (err) {
        dispatch(getFireCentreInfoFailed((err as Error).toString()));
        console.error(err);
      }
    } else {
      // We're offline so there is nothing to do but set the error state.
      dispatch(
        getFireCentreInfoFailed(
          "Unable to refresh fire centre info data. Data may be stale.",
        ),
      );
    }
  };

export const checkPushNotificationPermission =
  (): AppThunk => async (dispatch) => {
    try {
      const permissions = await FirebaseMessaging.checkPermissions();
      dispatch(setPushNotificationPermission(permissions.receive ?? "unknown"));
    } catch (e) {
      console.error(e);
      dispatch(setPushNotificationPermission("unknown"));
    }
  };
