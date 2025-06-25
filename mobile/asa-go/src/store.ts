import { Action, configureStore, ThunkAction } from "@reduxjs/toolkit";
import provincialSummarySlice from "@/slices/provincialSummarySlice";
import fireZoneElevationInfoSlice from "@/slices/fireZoneElevationInfoSlice";
import fireShapeAreasSlice from "@/slices/fireZoneAreasSlice";
import fireCentreTPIStatsSlice from "@/slices/fireCentreTPIStatsSlice";
import fireCentreHFIFuelStatsSlice from "@/slices/fireCentreHFIFuelStatsSlice";
import runDatesSlice from "@/slices/runDatesSlice";
import fireCentersSlice from "@/slices/fireCentersSlice";
import networkStatusSlice from "@/slices/networkStatusSlice";
import authenticationSlice from "@/slices/authenticationSlice";

export const store = configureStore({
  reducer: {
    fireCenters: fireCentersSlice,
    provincialSummary: provincialSummarySlice,
    fireZoneElevationInfo: fireZoneElevationInfoSlice,
    fireShapeAreas: fireShapeAreasSlice,
    fireCentreTPIStats: fireCentreTPIStatsSlice,
    fireCentreHFIFuelStats: fireCentreHFIFuelStatsSlice,
    runDates: runDatesSlice,
    networkStatus: networkStatusSlice,
    authentication: authenticationSlice,
  },
});

// Infer the `RootState` and `AppDispatch` types from the store itself
export type RootState = ReturnType<typeof store.getState>;
// Inferred type: {posts: PostsState, comments: CommentsState, users: UsersState}
export type AppDispatch = typeof store.dispatch;

export type AppThunk = ThunkAction<void, RootState, undefined, Action>;

export const selectRunDates = (state: RootState) => state.runDates;
export const selectFireShapeAreas = (state: RootState) => state.fireShapeAreas;
export const selectFireCenters = (state: RootState) => state.fireCenters;
export const selectNetworkStatus = (state: RootState) => state.networkStatus;
export const selectAuthentication = (state: RootState) => state.authentication;
export const selectToken = (state: RootState) => state.authentication.token;
