import { today } from "@/utils/dataSliceUtils";
import { AppThunk } from "@/store";
import {
  FIRE_CENTRES_CACHE_EXPIRATION,
  FIRE_CENTRES_KEY,
  readFromFilesystem,
  writeToFileSystem,
} from "@/utils/storage";
import { Filesystem } from "@capacitor/filesystem";
import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { getFireCentres } from "api/psuAPI";
import type { FireCentre } from "@/types/fireCentre";
import { isNull } from "lodash";
import { DateTime } from "luxon";

export interface FireCentresState {
  loading: boolean;
  error: string | null;
  fireCentres: FireCentre[];
}

export const initialState: FireCentresState = {
  loading: false,
  error: null,
  fireCentres: [],
};

const fireCentresSlice = createSlice({
  name: "fireCentres",
  initialState,
  reducers: {
    getFireCentresStart(state: FireCentresState) {
      state.error = null;
      state.loading = true;
      state.fireCentres = [];
    },
    getFireCentresFailed(
      state: FireCentresState,
      action: PayloadAction<string>,
    ) {
      state.error = action.payload;
      state.loading = false;
    },
    getFireCentresSuccess(
      state: FireCentresState,
      action: PayloadAction<FireCentre[]>,
    ) {
      state.error = null;
      state.fireCentres = action.payload;
      state.loading = false;
    },
  },
});

export const {
  getFireCentresStart,
  getFireCentresFailed,
  getFireCentresSuccess,
} = fireCentresSlice.actions;

export default fireCentresSlice.reducer;

export const fetchFireCentres = (): AppThunk => async (dispatch, getState) => {
  // Check for cached fire centers data. If the data is not stale save it in redux state.
  const cachedFireCentres = await readFromFilesystem(
    Filesystem,
    FIRE_CENTRES_KEY,
  );
  const networkStatus = getState().networkStatus;
  if (!isNull(cachedFireCentres)) {
    const lastUpdated = DateTime.fromISO(cachedFireCentres.lastUpdated);
    // Update state from the cached data if it isn't stale or if we're offline.
    if (
      lastUpdated.plus({ hours: FIRE_CENTRES_CACHE_EXPIRATION }) > today ||
      !networkStatus.networkStatus.connected
    ) {
      dispatch(getFireCentresSuccess(cachedFireCentres.data as FireCentre[]));
      return;
    }
  }
  // Cached data is not available or is stale so we need to fetch and cache if we're online.
  if (networkStatus.networkStatus.connected) {
    try {
      dispatch(getFireCentresStart());
      const fireCentres = await getFireCentres();
      await writeToFileSystem(
        Filesystem,
        FIRE_CENTRES_KEY,
        fireCentres.fire_centres,
        today,
      );
      dispatch(getFireCentresSuccess(fireCentres.fire_centres));
    } catch (err) {
      dispatch(getFireCentresFailed((err as Error).toString()));
      console.log(err);
    }
  } else {
    // We're offline so there is nothing to do but set the error state.
    dispatch(
      getFireCentresFailed(
        "Unable to refresh fire centre data. Data may be stale.",
      ),
    );
  }
};
