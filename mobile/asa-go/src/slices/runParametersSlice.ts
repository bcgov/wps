import { getTodayKey, getTomorrowKey, today } from "@/utils/dataSliceUtils";
import { AppDispatch, AppThunk, RootState } from "@/store";
import {
  readFromFilesystem,
  RUN_PARAMETERS_CACHE_KEY,
  writeToFileSystem,
} from "@/utils/storage";
import { Filesystem } from "@capacitor/filesystem";
import { createSelector, createSlice, PayloadAction } from "@reduxjs/toolkit";
import { getMostRecentRunParameters, RunParameter } from "api/fbaAPI";
import { isNil } from "lodash";
import { setLastUpdated } from "@/slices/dataSlice";
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
      action: PayloadAction<string>,
    ) {
      state.error = action.payload;
      state.loading = false;
    },
    getRunParametersSuccess(
      state: RunParametersState,
      action: PayloadAction<{
        runParameters: { [key: string]: RunParameter };
      }>,
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

const handleOnlineRunParameters = async (
  dispatch: AppDispatch,
  todayKey: string,
  tomorrowKey: string,
  reduxRunParameters: { [key: string]: RunParameter } | null,
) => {
  try {
    dispatch(getRunParametersStart());
    const latestRunParameters: { [key: string]: RunParameter } =
      await getMostRecentRunParameters(todayKey, tomorrowKey);

    if (isNil(latestRunParameters) || Object.keys(latestRunParameters).length === 0) {
      dispatch(getRunParametersFailed("Unable to update runParameters from the API."));
      return;
    }

    await writeToFileSystem(Filesystem, RUN_PARAMETERS_CACHE_KEY, latestRunParameters, today);

    if (isNil(reduxRunParameters) || stateUpdateRequired(todayKey, tomorrowKey, reduxRunParameters, latestRunParameters)) {
      dispatch(getRunParametersSuccess({ runParameters: latestRunParameters }));
    } else {
      dispatch(setLastUpdated({ lastUpdated: DateTime.now().toISO() }));
    }
  } catch (err) {
    dispatch(getRunParametersFailed((err as Error).toString()));
    console.log(err);
  }
};

const handleOfflineRunParameters = async (
  dispatch: AppDispatch,
  todayKey: string,
  tomorrowKey: string,
  reduxRunParameters: { [key: string]: RunParameter } | null,
) => {
  const cachedData = await readFromFilesystem(Filesystem, RUN_PARAMETERS_CACHE_KEY);
  const cachedRunParameters: { [key: string]: RunParameter } | null = isNil(cachedData)
    ? null
    : (cachedData.data as { [key: string]: RunParameter });

  if (isNil(cachedRunParameters)) {
    dispatch(getRunParametersFailed("No run parameters available."));
    return;
  }

  if (isNil(reduxRunParameters) || stateUpdateRequired(todayKey, tomorrowKey, reduxRunParameters, cachedRunParameters)) {
    dispatch(getRunParametersSuccess({ runParameters: cachedRunParameters }));
  }
};

export const fetchSFMSRunParameters =
  (): AppThunk => async (dispatch, getState) => {
    const todayKey = getTodayKey();
    const tomorrowKey = getTomorrowKey();
    const state = getState();
    const connected = state.networkStatus.networkStatus.connected;
    const reduxRunParameters = state.runParameters.runParameters;

    if (connected) {
      await handleOnlineRunParameters(dispatch, todayKey, tomorrowKey, reduxRunParameters);
    } else {
      await handleOfflineRunParameters(dispatch, todayKey, tomorrowKey, reduxRunParameters);
    }
  };

export const selectRunParameters = (state: RootState) =>
  state.runParameters.runParameters;

export const selectRunParameterByForDate = (forDate: string) =>
  createSelector([selectRunParameters], (runParameters) =>
    isNil(runParameters) ? null : runParameters[forDate],
  );

const stateUpdateRequired = (
  todayKey: string,
  tomorrowKey: string,
  a: { [key: string]: RunParameter },
  b: { [key: string]: RunParameter },
) => {
  return (
    !runParametersAreEqual(a[todayKey], b[todayKey]) ||
    !runParametersAreEqual(a[tomorrowKey], b[tomorrowKey])
  );
};

const runParametersAreEqual = (
  a: RunParameter | undefined,
  b: RunParameter | undefined,
) => {
  if (isNil(a) || isNil(b)) {
    return isNil(a) && isNil(b);
  }
  return (
    a.for_date === b.for_date &&
    a.run_datetime === b.run_datetime &&
    a.run_type === b.run_type
  );
};
