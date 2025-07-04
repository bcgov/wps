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

export const selectRunDates = (state: RootState) => state.runDates;
export const selectFireShapeAreas = (state: RootState) => state.fireShapeAreas;
export const selectFireCenters = (state: RootState) => state.fireCenters;
export const selectNetworkStatus = (state: RootState) => state.networkStatus;
export const selectGeolocation = (state: RootState) => state.geolocation;
