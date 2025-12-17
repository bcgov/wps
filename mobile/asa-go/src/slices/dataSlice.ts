import { AppThunk } from "@/store";
import {
  dataAreEqual,
  fetchHFIStats,
  fetchProvincialSummaries,
  fetchTpiStats,
  getTodayKey,
  getTomorrowKey,
  runParametersMatch,
  today,
} from "@/utils/dataSliceUtils";
import {
  CacheableData,
  CachedData,
  HFI_STATS_KEY,
  PROVINCIAL_SUMMARY_KEY,
  readFromFilesystem,
  TPI_STATS_KEY,
  writeToFileSystem,
} from "@/utils/storage";
import { Filesystem } from "@capacitor/filesystem";
import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import {
  FireShapeStatusDetail,
  FireZoneHFIStatsDictionary,
  FireZoneTPIStats,
} from "api/fbaAPI";
import { isNil } from "lodash";
import { DateTime } from "luxon";

export interface DataState {
  loading: boolean;
  error: string | null;
  lastUpdated: string | null;
  provincialSummaries: CacheableData<FireShapeStatusDetail[]> | null;
  tpiStats: CacheableData<FireZoneTPIStats[]> | null;
  hfiStats: CacheableData<FireZoneHFIStatsDictionary> | null;
}

export const initialState: DataState = {
  loading: false,
  error: null,
  lastUpdated: null,
  provincialSummaries: null,
  tpiStats: null,
  hfiStats: null,
};

const dataSlice = createSlice({
  name: "data",
  initialState,
  reducers: {
    getDataStart(state: DataState) {
      state.error = null;
      state.loading = true;
    },
    getDataFailed(state: DataState, action: PayloadAction<string>) {
      state.error = action.payload;
      state.loading = false;
    },
    getDataSuccess(
      state: DataState,
      action: PayloadAction<{
        lastUpdated: string;
        provincialSummaries: CacheableData<FireShapeStatusDetail[]> | null;
        tpiStats: CacheableData<FireZoneTPIStats[]> | null;
        hfiStats: CacheableData<FireZoneHFIStatsDictionary> | null;
      }>
    ) {
      state.error = null;
      state.lastUpdated = action.payload.lastUpdated;
      state.provincialSummaries = action.payload.provincialSummaries;
      state.tpiStats = action.payload.tpiStats;
      state.hfiStats = action.payload.hfiStats;
      state.loading = false;
    },
  },
});

export const { getDataStart, getDataFailed, getDataSuccess } =
  dataSlice.actions;

export default dataSlice.reducer;

export const fetchAndCacheData = (): AppThunk => async (dispatch, getState) => {
  const todayKey = getTodayKey();
  const tomorrowKey = getTomorrowKey();
  const state = getState();
  const runParameters = state.runParameters.runParameters;
  let isCurrent = true; // A flag indicating if the cached data and state are current
  if (isNil(runParameters)) {
    dispatch(
      getDataFailed(
        "Unable to fetch and cache data; runParameters can't be null."
      )
    );
    return;
  }
  // Grab cached data and check if we have cached data for the run parameters in state, if so, set
  // redux state with this data.
  const cachedProvincialSummaries = (await readFromFilesystem(
    Filesystem,
    PROVINCIAL_SUMMARY_KEY
  )) as CachedData<CacheableData<FireShapeStatusDetail[]>>;
  isCurrent =
    isCurrent &&
    !isNil(cachedProvincialSummaries?.data) &&
    runParametersMatch(
      todayKey,
      tomorrowKey,
      runParameters,
      cachedProvincialSummaries.data
    );

  const cachedTPIStats = (await readFromFilesystem(
    Filesystem,
    TPI_STATS_KEY
  )) as CachedData<CacheableData<FireZoneTPIStats[]>>;
  isCurrent =
    isCurrent &&
    !isNil(cachedTPIStats?.data) &&
    runParametersMatch(
      todayKey,
      tomorrowKey,
      runParameters,
      cachedTPIStats.data
    );

  const cachedHFIStats = (await readFromFilesystem(
    Filesystem,
    HFI_STATS_KEY
  )) as CachedData<CacheableData<FireZoneHFIStatsDictionary>>;
  isCurrent =
    isCurrent &&
    !isNil(cachedHFIStats?.data) &&
    runParametersMatch(
      todayKey,
      tomorrowKey,
      runParameters,
      cachedHFIStats.data
    );

  if (isCurrent) {
    // No need to fetch new data, compare cached data to state data to see if state update required
    const stateProvincialSummaries = state.data.provincialSummaries;
    const stateTPIStats = state.data.tpiStats;
    const stateHFIStats = state.data.hfiStats;
    if (
      !dataAreEqual(stateProvincialSummaries, cachedProvincialSummaries.data) &&
      !dataAreEqual(stateTPIStats, cachedTPIStats.data) &&
      !dataAreEqual(stateHFIStats, cachedHFIStats.data)
    ) {
      // Update state from cached data if required
      dispatch(
        getDataSuccess({
          lastUpdated: DateTime.now().toISO(),
          provincialSummaries: cachedProvincialSummaries.data,
          tpiStats: cachedTPIStats.data,
          hfiStats: cachedHFIStats.data,
        })
      );
    }
    return;
  }

  // Cached data is not available or is stale so we need to fetch and cache if we're online.
  const { networkStatus } = getState().networkStatus;
  if (networkStatus.connected) {
    try {
      dispatch(getDataStart());
      const provincialSummaries = await fetchProvincialSummaries(
        todayKey,
        tomorrowKey,
        runParameters
      );
      const tpiStats = await fetchTpiStats(
        todayKey,
        tomorrowKey,
        runParameters
      );
      const hfiStats = await fetchHFIStats(
        todayKey,
        tomorrowKey,
        runParameters
      );

      // Should we validate the new data in some way or assume a happy path?
      // Write all new data to cache
      await writeToFileSystem(
        Filesystem,
        PROVINCIAL_SUMMARY_KEY,
        provincialSummaries,
        today
      );
      await writeToFileSystem(Filesystem, TPI_STATS_KEY, tpiStats, today);
      await writeToFileSystem(Filesystem, HFI_STATS_KEY, hfiStats, today);

      // Update state
      dispatch(
        getDataSuccess({
          lastUpdated: DateTime.now().toISO(),
          provincialSummaries,
          tpiStats,
          hfiStats,
        })
      );
    } catch (err) {
      dispatch(getDataFailed((err as Error).toString()));
      console.error(err);
    }
  } else {
    dispatch(getDataFailed("Unable to update data. Data may be stale."));
  }
};
