import { today } from "@/utils/dataSliceUtils";
import { AppThunk } from "@/store";
import {
  FIRE_CENTERS_CACHE_EXPIRATION,
  FIRE_CENTERS_KEY,
  readFromFilesystem,
  writeToFileSystem,
} from "@/utils/storage";
import { Filesystem } from "@capacitor/filesystem";
import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { FireCenter, getFBAFireCenters } from "api/fbaAPI";
import { isNull } from "lodash";
import { DateTime } from "luxon";

export interface FireCentresState {
  loading: boolean;
  error: string | null;
  fireCenters: FireCenter[];
}

export const initialState: FireCentresState = {
  loading: false,
  error: null,
  fireCenters: [],
};

const fireCentersSlice = createSlice({
  name: "fireCenters",
  initialState,
  reducers: {
    getFireCentersStart(state: FireCentresState) {
      state.error = null;
      state.loading = true;
      state.fireCenters = [];
    },
    getFireCentersFailed(
      state: FireCentresState,
      action: PayloadAction<string>
    ) {
      state.error = action.payload;
      state.loading = false;
    },
    getFireCentersSuccess(
      state: FireCentresState,
      action: PayloadAction<FireCenter[]>
    ) {
      state.error = null;
      state.fireCenters = action.payload;
      state.loading = false;
    },
  },
});

export const {
  getFireCentersStart,
  getFireCentersFailed,
  getFireCentersSuccess,
} = fireCentersSlice.actions;

export default fireCentersSlice.reducer;

export const fetchFireCenters = (): AppThunk => async (dispatch, getState) => {
  // Check for cached fire centers data. If the data is not stale save it in redux state.
  const cachedFireCenters = await readFromFilesystem(
    Filesystem,
    FIRE_CENTERS_KEY
  );
  if (!isNull(cachedFireCenters)) {
    const lastUpdated = DateTime.fromISO(cachedFireCenters.lastUpdated);
    if (lastUpdated.plus({ hours: FIRE_CENTERS_CACHE_EXPIRATION }) > today) {
      dispatch(getFireCentersSuccess(cachedFireCenters.data));
      return;
    }
  }
  // Cached data is not available or is stale so we need to fetch and cache if we're online.
  const networkStatus = getState().networkStatus;
  if (networkStatus.networkStatus.connected) {
    try {
      dispatch(getFireCentersStart());
      const fireCenters = await getFBAFireCenters();
      await writeToFileSystem(
        Filesystem,
        FIRE_CENTERS_KEY,
        fireCenters.fire_centers,
        today
      );
      dispatch(getFireCentersSuccess(fireCenters.fire_centers));
    } catch (err) {
      dispatch(getFireCentersFailed((err as Error).toString()));
      console.log(err);
    }
  } else {
    // We're offline so there is nothing to do but set the error state.
    dispatch(
      getFireCentersFailed(
        "Unable to refresh fire center data. Data may be stale."
      )
    );
  }
};
