import { Action, configureStore, ThunkAction } from "@reduxjs/toolkit";
import provincialSummarySlice from "@/slices/provincialSummarySlice";
import fireZoneElevationInfoSlice from "@/slices/fireZoneElevationInfoSlice";
import fireShapeAreasSlice from "@/slices/fireZoneAreasSlice";
import fireCentreTPIStatsSlice from "@/slices/fireCentreTPIStatsSlice";
import fireCentreHFIFuelStatsSlice from "@/slices/fireCentreHFIFuelStatsSlice";
import runParameterSlice from "@/slices/runParameterSlice";
import fireCentersSlice from "@/slices/fireCentersSlice";
import networkStatusSlice from "@/slices/networkStatusSlice"

export const store = configureStore({
  reducer: {
    fireCenters: fireCentersSlice,
    provincialSummary: provincialSummarySlice,
    fireZoneElevationInfo: fireZoneElevationInfoSlice,
    fireShapeAreas: fireShapeAreasSlice,
    fireCentreTPIStats: fireCentreTPIStatsSlice,
    fireCentreHFIFuelStats: fireCentreHFIFuelStatsSlice,
    runParameter: runParameterSlice,
    networkStatus: networkStatusSlice
  },
});

// Infer the `RootState` and `AppDispatch` types from the store itself
export type RootState = ReturnType<typeof store.getState>;
// Inferred type: {posts: PostsState, comments: CommentsState, users: UsersState}
export type AppDispatch = typeof store.dispatch;

export type AppThunk = ThunkAction<void, RootState, undefined, Action>;

export const selectRunParameter = (state: RootState) => state.runParameter;
export const selectFireShapeAreas = (state: RootState) => state.fireShapeAreas;
export const selectFireCenters = (state: RootState) => state.fireCenters;
export const selectNetworkStatus = (state: RootState) => state.networkStatus
