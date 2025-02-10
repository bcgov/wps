import { Action, configureStore, ThunkAction } from "@reduxjs/toolkit";
import counterReducer from "@/slices/counterSlice";
import provincialSummarySlice from "@/slices/provincialSummarySlice";
import fireZoneElevationInfoSlice from "@/slices/fireZoneElevationInfoSlice";
import fireShapeAreasSlice from "@/slices/fireZoneAreasSlice";
import fireCentreTPIStatsSlice from "@/slices/fireCentreTPIStatsSlice";
import fireCentreHFIFuelStatsSlice from "@/slices/fireCentreHFIFuelStatsSlice";

export const store = configureStore({
  reducer: {
    counter: counterReducer,
    provincialSummary: provincialSummarySlice,
    fireZoneElevationInfo: fireZoneElevationInfoSlice,
    fireShapeAreas: fireShapeAreasSlice,
    fireCentreTPIStats: fireCentreTPIStatsSlice,
    fireCentreHFIFuelStats: fireCentreHFIFuelStatsSlice,
  },
});

// Infer the `RootState` and `AppDispatch` types from the store itself
export type RootState = ReturnType<typeof store.getState>;
// Inferred type: {posts: PostsState, comments: CommentsState, users: UsersState}
export type AppDispatch = typeof store.dispatch;

export type AppThunk = ThunkAction<void, RootState, undefined, Action>;

export const countSelector = (state: RootState) => state.counter.value;
