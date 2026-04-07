import { rootReducer } from "@/rootReducer";
import {
  Action,
  configureStore,
  createSelector,
  ThunkAction,
} from "@reduxjs/toolkit";

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
export const selectTPIStats = (state: RootState) => state.data.tpiStats;
export const selectHFIStats = (state: RootState) => state.data.hfiStats;
export const selectSettings = (state: RootState) => state.settings;
export const selectPushNotification = (state: RootState) => state.pushNotification;

export type NotificationSetupState =
  | "permissionDenied"
  | "unregistered"
  | "registrationFailed"
  | "ready";

export const selectNotificationSetupState = createSelector(
  selectPushNotification,
  ({
    pushNotificationPermission,
    registeredFcmToken,
    registrationError,
  }): NotificationSetupState => {
    if (pushNotificationPermission !== "granted") {
      return "permissionDenied";
    }
    if (!registeredFcmToken) {
      return registrationError ? "registrationFailed" : "unregistered";
    }
    return "ready";
  },
);

export const selectNotificationSettingsDisabled = createSelector(
  selectNotificationSetupState,
  selectNetworkStatus,
  selectSettings,
  (setupState, { networkStatus }, { subscriptionsInitialized }) =>
    setupState !== "ready" || !networkStatus.connected || !subscriptionsInitialized,
);

