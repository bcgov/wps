import { AppThunk } from "@/store";
import {
  CacheableData,
  CacheableDataType,
  FIRE_SHAPE_AREAS_KEY,
  PROVINCIAL_SUMMARY_KEY,
  readFromFilesystem,
  writeToFileSystem,
} from "@/utils/storage";
import { Filesystem } from "@capacitor/filesystem";
import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import {
  FireShapeArea,
  FireShapeAreaDetail,
  getFireShapeAreas,
  getProvincialSummary,
  RunParameter,
} from "api/fbaAPI";
import { isEqual, isNil } from "lodash";
import { DateTime } from "luxon";

export interface DataState {
  loading: boolean;
  error: string | null;
  lastUpdated: string | null;
  fireShapeAreas: CacheableData<FireShapeArea[]> | null;
  provincialSummaries: CacheableData<FireShapeAreaDetail[]> | null;
}

export const initialState: DataState = {
  loading: false,
  error: null,
  lastUpdated: null,
  provincialSummaries: null,
  fireShapeAreas: null,
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
        fireShapeAreas: CacheableData<FireShapeArea[]> | null;
        provincialSummaries: CacheableData<FireShapeAreaDetail[]>;
      }>
    ) {
      state.error = null;
      state.lastUpdated = action.payload.lastUpdated;
      state.fireShapeAreas = action.payload.fireShapeAreas;
      state.provincialSummaries = action.payload.provincialSummaries;
      state.loading = false;
    },
  },
});

export const { getDataStart, getDataFailed, getDataSuccess } =
  dataSlice.actions;

export default dataSlice.reducer;

export const fetchAndCacheData = (): AppThunk => async (dispatch, getState) => {
  const today = DateTime.now();
  const tomorrow = today.plus({ days: 1 });
  const todayKey = today.toISODate();
  const tomorrowKey = tomorrow.toISODate();
  const state = getState();
  const runParameters = state.runParameters.runParameters;
  let isCurrent = true; // A flag indicating if the cached data and state are current
  if (isNil(runParameters)) {
    // Run parameters are required to fetch data. Should this be an error state?
    return;
  }
  // Grab cached data and check if we have cached data for the run parameters in state, if so, set
  // redux state with this data.
  const cachedProvincialSummaries = await readFromFilesystem(
    Filesystem,
    PROVINCIAL_SUMMARY_KEY
  );
  isCurrent =
    !isNil(cachedProvincialSummaries?.data) &&
    runParametersMatch(
      todayKey,
      tomorrowKey,
      runParameters,
      cachedProvincialSummaries.data
    );

  const cachedFireShapeAreas = await readFromFilesystem(
    Filesystem,
    FIRE_SHAPE_AREAS_KEY
  );
  isCurrent =
    !isNil(cachedFireShapeAreas?.data) &&
    runParametersMatch(
      todayKey,
      tomorrowKey,
      runParameters,
      cachedFireShapeAreas.data
    );

  if (isCurrent) {
    // No need to fetch new data, compare cached data to state data to see if state update required
    const stateProvincialSummaries = state.data.provincialSummaries;
    const stateFireShapeAreas = state.data.fireShapeAreas;
    if (
      !dataAreEqual(stateProvincialSummaries, cachedProvincialSummaries.data) &&
      !dataAreEqual(stateFireShapeAreas, cachedFireShapeAreas.data)
    ) {
      dispatch(
        getDataSuccess({
          lastUpdated: DateTime.now().toISODate(),
          fireShapeAreas: cachedFireShapeAreas.data,
          provincialSummaries: cachedProvincialSummaries.data,
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
      const fireShapeAreas = await fetchFireShapeAreas(
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

      await writeToFileSystem(
        Filesystem,
        FIRE_SHAPE_AREAS_KEY,
        fireShapeAreas,
        today
      );

      // Update state
      dispatch(
        getDataSuccess({
          lastUpdated: DateTime.now().toISODate(),
          fireShapeAreas: fireShapeAreas,
          provincialSummaries,
        })
      );
      return;
    } catch (err) {
      dispatch(getDataFailed((err as Error).toString()));
      console.error(err);
    }
  }
  dispatch(getDataFailed("Unable to update data. Data may be stale."));
};

const runParametersMatch = (
  todayKey: string,
  tomorrowKey: string,
  runParameters: { [key: string]: RunParameter },
  data: CacheableData<CacheableDataType>
): boolean => {
  return (
    isEqual(runParameters[todayKey], data[todayKey].runParameter) &&
    isEqual(runParameters[tomorrowKey], data[tomorrowKey].runParameter)
  );
};

const fetchFireShapeAreas = async (
  todayKey: string,
  tomorrowKey: string,
  runParameters: { [key: string]: RunParameter }
): Promise<CacheableData<FireShapeArea[]>> => {
  // API calls to get data for today and tomorrow
  const todayFireShapeArea = await fetchFireShapeArea(runParameters[todayKey]);
  const tomorrowFireShapeArea = await fetchFireShapeArea(
    runParameters[tomorrowKey]
  );
  const fireShapeAreas = shapeDataForCaching(
    todayKey,
    tomorrowKey,
    runParameters,
    todayFireShapeArea,
    tomorrowFireShapeArea
  );
  return fireShapeAreas;
};

const fetchProvincialSummaries = async (
  todayKey: string,
  tomorrowKey: string,
  runParameters: { [key: string]: RunParameter }
): Promise<CacheableData<FireShapeAreaDetail[]>> => {
  // API calls to get data for today and tomorrow
  const todayProvincialSummary = await fetchProvincialSummary(
    runParameters[todayKey]
  );
  const tomorrowProvincialSummary = await fetchProvincialSummary(
    runParameters[tomorrowKey]
  );
  // Shape the data for caching and storing in state
  const provincialSummaries = {
    [todayKey]: {
      runParameter: runParameters[todayKey],
      data: todayProvincialSummary,
    },
    [tomorrowKey]: {
      runParameter: runParameters[tomorrowKey],
      data: tomorrowProvincialSummary,
    },
  };

  return provincialSummaries;
};

const shapeDataForCaching = (
  todayKey: string,
  tomorrowKey: string,
  runParameters: { [key: string]: RunParameter },
  todayData: CacheableDataType,
  tomorrowData: CacheableDataType
): CacheableData<CacheableDataType> => {
  return {
    [todayKey]: {
      runParameter: runParameters[todayKey],
      data: todayData,
    },
    [tomorrowKey]: {
      runParameter: runParameters[tomorrowKey],
      data: tomorrowData,
    },
  };
};

const fetchFireShapeArea = async (runParameter: RunParameter) => {
  const fireShapeArea = await getFireShapeAreas(
    runParameter.run_type,
    runParameter.run_datetime,
    runParameter.for_date
  );
  return fireShapeArea?.shapes;
};

const fetchProvincialSummary = async (runParameter: RunParameter) => {
  const provincialSummary = await getProvincialSummary(
    runParameter.run_type,
    runParameter.run_datetime,
    runParameter.for_date
  );
  return provincialSummary?.provincial_summary;
};

const dataAreEqual = (
  a: CacheableData<CacheableDataType> | null,
  b: CacheableData<CacheableDataType> | null
): boolean => {
  return isEqual(a, b);
};

// const selectFireShapeAreaDetails = (state: RootState) => state.data;

// export const selectProvincialSummary = createSelector(
//   [selectFireShapeAreaDetails],
//   (fireShapeAreaDetails) => {
//     const groupedByFireCenter = groupBy(
//       fireShapeAreaDetails.fireShapeAreaDetails,
//       "fire_centre_name"
//     );
//     return groupedByFireCenter;
//   }
// );

// const fetchAndCacheProvincialSummaries = async (
//   todayKey: string,
//   tomorrowKey: string,
//   runParameters: { [key: string]: RunParameter }
// ): Promise<CacheableData<CacheableDataType>> => {
//   // API calls to get data for today and tomorrow
//   const todayProvincialSummary = await fetchProvincialSummary(
//     runParameters[todayKey]
//   );
//   const tomorrowProvincialSummary = await fetchProvincialSummary(
//     runParameters[tomorrowKey]
//   );
//   // Shape the data for caching
//   const cacheableSummaries = {
//     [todayKey]: {
//       runParameter: runParameters[todayKey],
//       data: todayProvincialSummary,
//     },
//     [tomorrowKey]: {
//       runParameter: runParameters[tomorrowKey],
//       data: tomorrowProvincialSummary,
//     },
//   };
//   // Cache the data
//   await writeToFileSystem(Filesystem, PROVINCIAL_SUMMARY_KEY, cacheableSummaries, DateTime.now())
//   return cacheableSummaries
// };
