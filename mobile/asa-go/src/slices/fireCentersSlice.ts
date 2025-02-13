import { createSlice, PayloadAction } from "@reduxjs/toolkit";

import { AppThunk } from "@/store";
import { FBAResponse, FireCenter, getFBAFireCenters } from "api/fbaAPI";

export interface FireCentresState {
  loading: boolean;
  error: string | null;
  fireCenters: FireCenter[];
}

const initialState: FireCentresState = {
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
      action: PayloadAction<FBAResponse>
    ) {
      state.error = null;
      state.fireCenters = action.payload.fire_centers;
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

export const fetchFireCenters = (): AppThunk => async (dispatch) => {
  try {
    dispatch(getFireCentersStart());
    const fireCenters = await getFBAFireCenters();
    dispatch(getFireCentersSuccess(fireCenters));
  } catch (err) {
    dispatch(getFireCentersFailed((err as Error).toString()));
    console.log(err);
  }
};
