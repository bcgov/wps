import { AppThunk } from "@/store";
import { today } from "@/utils/dataSliceUtils";
import {
  FIRE_CENTER_INFO_CACHE_EXPIRATION,
  FIRE_CENTER_INFO_KEY,
  readFromFilesystem,
  writeToFileSystem,
} from "@/utils/storage";
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
  subscriptions: number[];
}

export const initialState: SettingsState = {
  loading: false,
  error: null,
  fireCentreInfos: [],
  pinnedFireCentre: null,
  subscriptions: [],
};

const PINNED_FIRE_CENTRE_KEY = "asaGoPinnedFireCentre";
const SUBSCRIPTIONS_KEY = "asaGoSubscriptions";

const settingsSlice = createSlice({
  name: "settings",
  initialState,
  reducers: {
    getFireCenterInfoStart(state: SettingsState) {
      state.error = null;
      state.loading = true;
      state.fireCentreInfos = [];
    },
    getFireCenterInfoFailed(
      state: SettingsState,
      action: PayloadAction<string>,
    ) {
      state.error = action.payload;
      state.loading = false;
    },
    getFireCenterInfoSuccess(
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
    setSubscriptions(state: SettingsState, action: PayloadAction<number[]>) {
      state.subscriptions = action.payload;
    },
  },
});

export const {
  getFireCenterInfoStart,
  getFireCenterInfoFailed,
  getFireCenterInfoSuccess,
  setPinnedFireCentre,
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
      if (subs) {
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

// Update @capacitor/preferences and redux state with pinned fire centre
export const savePinnedFireCentre =
  (fireCentre: string | null): AppThunk =>
  async (dispatch) => {
    if (isNull(fireCentre)) {
      await Preferences.remove({ key: PINNED_FIRE_CENTRE_KEY });
    } else {
      await Preferences.set({
        key: PINNED_FIRE_CENTRE_KEY,
        value: fireCentre ?? "",
      });
    }
    dispatch(setPinnedFireCentre(fireCentre));
  };

export const fetchFireCentreInfo =
  (): AppThunk => async (dispatch, getState) => {
    // Check for cached fire centers data. If the data is not stale save it in redux state.
    const cachedFireCenterInfo = await readFromFilesystem(
      Filesystem,
      FIRE_CENTER_INFO_KEY,
    );
    const networkStatus = getState().networkStatus;
    if (!isNull(cachedFireCenterInfo)) {
      const lastUpdated = DateTime.fromISO(cachedFireCenterInfo.lastUpdated);
      // Update state from the cached data if it isn't stale or if we're offline.
      if (
        lastUpdated.plus({ hours: FIRE_CENTER_INFO_CACHE_EXPIRATION }) >
          today ||
        !networkStatus.networkStatus.connected
      ) {
        dispatch(
          getFireCenterInfoSuccess(
            cachedFireCenterInfo.data as FireCentreInfo[],
          ),
        );
        return;
      }
    }
    // Cached data is not available or is stale so we need to fetch and cache if we're online.
    if (networkStatus.networkStatus.connected) {
      try {
        dispatch(getFireCenterInfoStart());
        const fireCenterInfo = await getFireCentreInfo();
        await writeToFileSystem(
          Filesystem,
          FIRE_CENTER_INFO_KEY,
          fireCenterInfo.fire_centre_info,
          today,
        );
        dispatch(getFireCenterInfoSuccess(fireCenterInfo.fire_centre_info));
      } catch (err) {
        dispatch(getFireCenterInfoFailed((err as Error).toString()));
        console.log(err);
      }
    } else {
      // We're offline so there is nothing to do but set the error state.
      dispatch(
        getFireCenterInfoFailed(
          "Unable to refresh fire center info data. Data may be stale.",
        ),
      );
    }
  };
