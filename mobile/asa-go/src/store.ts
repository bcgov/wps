import { rootReducer } from "@/rootReducer";
import { Action, configureStore, ThunkAction } from "@reduxjs/toolkit";

export const store = configureStore({
  reducer: rootReducer,
});

// Infer the `RootState` and `AppDispatch` types from the store itself
export type RootState = ReturnType<typeof store.getState>;
// Inferred type: {posts: PostsState, comments: CommentsState, users: UsersState}
export type AppDispatch = typeof store.dispatch;

export type AppThunk = ThunkAction<void, RootState, undefined, Action>;

export const selectFireCenters = (state: RootState) => state.fireCenters;
export const selectGeolocation = (state: RootState) => state.geolocation;
export const selectAuthentication = (state: RootState) => state.authentication;
export const selectNetworkStatus = (state: RootState) => state.networkStatus;
export const selectToken = (state: RootState) => state.authentication.token;
export const selectRunParameters = (state: RootState) =>
  state.runParameters.runParameters;
export const selectProvincialSummaries = (state: RootState) =>
  state.data.provincialSummaries;
export const selectFireShapeAreas = (state: RootState) =>
  state.data.fireShapeAreas;
export const selectTPIStats = (state: RootState) => state.data.tpiStats;
export const selectHFIStats = (state: RootState) => state.data.hfiStats;
