import { AppThunk, RootState } from "@/store";
import {
  readFromFilesystem,
  RUN_PARAMETERS_CACHE_KEY,
  writeToFileSystem,
} from "@/utils/storage";
import { Filesystem } from "@capacitor/filesystem";
import { createSelector, createSlice, PayloadAction } from "@reduxjs/toolkit";
import { getMostRecentRunParameters, RunParameter } from "api/fbaAPI";
import { isNil } from "lodash";
import { DateTime } from "luxon";

export interface RunParametersState {
  loading: boolean;
  error: string | null;
  runParameters: { [key: string]: RunParameter } | null;
}

export const initialState: RunParametersState = {
  loading: false,
  error: null,
  runParameters: null,
};

const runParameterSlice = createSlice({
  name: "runParameters",
  initialState,
  reducers: {
    getRunParametersStart(state: RunParametersState) {
      state.error = null;
      state.loading = true;
    },
    getRunParametersFailed(
      state: RunParametersState,
      action: PayloadAction<string>
    ) {
      state.error = action.payload;
      state.loading = false;
    },
    getRunParametersSuccess(
      state: RunParametersState,
      action: PayloadAction<{
        runParameters: { [key: string]: RunParameter };
      }>
    ) {
      state.error = null;
      state.runParameters = action.payload.runParameters;
      state.loading = false;
    },
  },
});

export const {
  getRunParametersStart,
  getRunParametersFailed,
  getRunParametersSuccess,
} = runParameterSlice.actions;

export default runParameterSlice.reducer;

export const fetchSFMSRunParameters =
  (): AppThunk => async (dispatch, getState) => {
    const now = DateTime.now();
    const todayKey = now.toISODate();
    const tomorrowKey = now.plus({ days: 1 }).toISODate();
    const state = getState();
    const connected = state.networkStatus.networkStatus.connected;
    const reduxRunParameters = state.runParameters.runParameters;
    if (connected) {
      // We're online so fetch SFMS run times from the API for today and tomorrow.
      try {
        dispatch(getRunParametersStart());
        const latestRunParameters: { [key: string]: RunParameter } =
          await getMostRecentRunParameters(todayKey, tomorrowKey);
        if (
          !isNil(latestRunParameters) &&
          !isNil(latestRunParameters[todayKey]) &&
          !isNil(latestRunParameters[tomorrowKey])
        ) {
          // Cache the run parameters for today and tomorrow
          await writeToFileSystem(
            Filesystem,
            RUN_PARAMETERS_CACHE_KEY,
            latestRunParameters,
            now
          );

          if (
            isNil(reduxRunParameters) ||
            stateUpdateRequired(
              todayKey,
              tomorrowKey,
              reduxRunParameters,
              latestRunParameters
            )
          ) {
            // Retrieved run parameters differ from redux state so update
            dispatch(
              getRunParametersSuccess({
                runParameters: latestRunParameters,
              })
            );
          }
        }
      } catch (err) {
        dispatch(getRunParametersFailed((err as Error).toString()));
        console.log(err);
      }
    } else {
      // We're offline, so check the cache for existing run parameters and update state with the
      // values read from the cache if they differ from the values currently in state.
      const cachedData = await readFromFilesystem(
        Filesystem,
        RUN_PARAMETERS_CACHE_KEY
      );
      const cachedRunParameters: { [key: string]: RunParameter } = !isNil(
        cachedData
      )
        ? cachedData.data
        : null;
      if (
        !isNil(cachedRunParameters) &&
        (isNil(reduxRunParameters) ||
          stateUpdateRequired(
            todayKey,
            tomorrowKey,
            reduxRunParameters,
            cachedRunParameters
          ))
      ) {
        // Retrieved run parameters for the specified date differ from redux state so update
        dispatch(
          getRunParametersSuccess({
            runParameters: cachedRunParameters,
          })
        );
      } else {
        // We're offline and there are no cached run parameters for today
        dispatch(getRunParametersFailed("No run parameters available."));
      }
    }
  };


export const selectRunParameters = (state: RootState) => state.runParameters.runParameters

export const selectRunParameterByForDate = (forDate: string) => {
  createSelector(
  [selectRunParameters], (runParameters) => {
    return isNil(runParameters) ? null : runParameters[forDate]
  })}  

const stateUpdateRequired = (
  todayKey: string,
  tomorrowKey: string,
  a: { [key: string]: RunParameter },
  b: { [key: string]: RunParameter }
) => {
  if (isNil(a[todayKey]) || isNil(a[tomorrowKey])) {
    return true;
  }
  if (isNil(b[todayKey]) || isNil(b[tomorrowKey])) {
    return false;
  }
  return (
    !runParametersAreEqual(a[todayKey], b[todayKey]) ||
    !runParametersAreEqual(a[tomorrowKey], b[tomorrowKey])
  );
};

const runParametersAreEqual = (a: RunParameter, b: RunParameter) => {
  return (
    a.for_date === b.for_date &&
    a.run_datetime === b.run_datetime &&
    a.run_type === b.run_type
  );
};