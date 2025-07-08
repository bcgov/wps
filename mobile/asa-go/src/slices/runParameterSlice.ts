import { AppThunk } from "@/store";
import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { getMostRecentRunParameter, RunType } from "api/fbaAPI";

export interface RunParameterState {
  loading: boolean;
  error: string | null;
  forDate: string | null;
  runDatetime: string | null;
  runType: RunType | null;
}

const initialState: RunParameterState = {
  loading: false,
  error: null,
  forDate: null,
  runDatetime: null,
  runType: null,
};

const runParameterSlice = createSlice({
  name: "runParameter",
  initialState,
  reducers: {
    getRunParameterStart(state: RunParameterState) {
      state.error = null;
      state.loading = true;
      state.forDate = null;
      state.runDatetime = null;
      state.runType = null;
    },
    getRunParameterFailed(
      state: RunParameterState,
      action: PayloadAction<string>
    ) {
      state.error = action.payload;
      state.loading = false;
      state.forDate = null;
      state.runDatetime = null;
      state.runType = null;
    },
    getRunParameterSuccess(
      state: RunParameterState,
      action: PayloadAction<{
        forDate: string;
        runDateTime: string;
        runType: RunType;
      }>
    ) {
      state.error = null;
      state.forDate = action.payload.forDate;
      state.runDatetime = action.payload.runDateTime;
      state.runType = action.payload.runType;
      state.loading = false;
    },
  },
});

export const {
  getRunParameterStart,
  getRunParameterFailed,
  getRunParameterSuccess,
} = runParameterSlice.actions;

export default runParameterSlice.reducer;

export const fetchMostRecentSFMSRunParameter =
  (forDate: string): AppThunk =>
  async (dispatch) => {
    try {
      dispatch(getRunParameterStart());
      const runParameter = await getMostRecentRunParameter(forDate);
      dispatch(
        getRunParameterSuccess({
          forDate: runParameter.for_date,
          runDateTime: runParameter.run_datetime,
          runType: runParameter.run_type,
        })
      );
    } catch (err) {
      dispatch(getRunParameterFailed((err as Error).toString()));
      console.log(err);
    }
  };
