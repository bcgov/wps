import { AppThunk } from "@/store";
import { Preferences } from "@capacitor/preferences";
import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { FireCentreInfo, getFireCentreInfo } from "api/fbaAPI";
import { isNil, isNull } from "lodash";

export interface SettingsState {
  loading: boolean;
  error: string | null;
  fireCentreInfos: FireCentreInfo[];
  pinnedFireCentre: string | null;
}

export const initialState: SettingsState = {
  loading: false,
  error: null,
  fireCentreInfos: [],
  pinnedFireCentre: null,
};

const PINNED_FIRE_CENTRE_KEY = "pinnedFireCentre";

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
  },
});

export const {
  getFireCenterInfoStart,
  getFireCenterInfoFailed,
  getFireCenterInfoSuccess,
  setPinnedFireCentre,
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

//
export const fetchFireCentreInfo = (): AppThunk => async (dispatch) => {
  try {
    dispatch(getFireCenterInfoStart());
    console.log("DEBUG: Making an API call to get settings info.");
    const fireCentreInfo = await getFireCentreInfo();
    dispatch(
      getFireCenterInfoSuccess(fireCentreInfo.fire_centre_info),
    );
  } catch (err) {
    dispatch(getFireCenterInfoFailed((err as Error).toString()));
    console.log(err);
  }
};
