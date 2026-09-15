import { type Action, configureStore, createSelector, type ThunkAction } from '@reduxjs/toolkit'
import { rootReducer } from '@/rootReducer'
import { getNotificationPriority } from '@/slices/notificationSlice'

export const store = configureStore({
  reducer: rootReducer
})

// Infer the `RootState` and `AppDispatch` types from the store itself
export type RootState = ReturnType<typeof store.getState>
// Inferred type: {posts: PostsState, comments: CommentsState, users: UsersState}
export type AppDispatch = typeof store.dispatch

export type AppThunk = ThunkAction<void, RootState, undefined, Action>

export const selectFireCentres = (state: RootState) => state.fireCentres
export const selectGeolocation = (state: RootState) => state.geolocation
export const selectAuthentication = (state: RootState) => state.authentication
export const selectFeedback = (state: RootState) => state.feedback
export const selectNetworkStatus = (state: RootState) => state.networkStatus
export const selectNotifications = (state: RootState) => state.notifications.notifications
export const selectCurrentNotification = createSelector(selectNotifications, notifications => {
  return notifications.reduce<(typeof notifications)[number] | null>((current, notification) => {
    if (!current || getNotificationPriority(notification) > getNotificationPriority(current)) {
      return notification
    }
    return current
  }, null)
})
export const selectToken = (state: RootState) => state.authentication.token
export const selectRunParameters = (state: RootState) => state.runParameters.runParameters
export const selectProvincialSummaries = (state: RootState) => state.data.provincialSummaries
export const selectTPIStats = (state: RootState) => state.data.tpiStats
export const selectHFIStats = (state: RootState) => state.data.hfiStats
export const selectSettings = (state: RootState) => state.settings
export const selectPushNotification = (state: RootState) => state.pushNotification
export const selectPendingNotificationData = (state: RootState) => state.pushNotification.pendingNotificationData
export const selectLastUpdated = (state: RootState) => state.data.lastUpdated

export interface LoadSourceState {
  loading: boolean
  errorKey: string | null
}

export const selectOperationalLoadState = createSelector(
  [
    (state: RootState) => state.fireCentres,
    (state: RootState) => state.runParameters,
    (state: RootState) => state.data
  ],
  (fireCentres, runParameters, data): LoadSourceState => {
    const operationalDataUnavailable =
      data.provincialSummaries === null || data.tpiStats === null || data.hfiStats === null
    const errorKey = [data.error, fireCentres.error, runParameters.error].filter(Boolean).join('|') || null

    // only expose run-parameter loading while the operational datasets are still being initialized
    return {
      loading: fireCentres.loading || data.loading || (runParameters.loading && operationalDataUnavailable),
      errorKey
    }
  }
)

export const selectOperationalDataLoading = createSelector(selectOperationalLoadState, ({ loading }) => loading)

export const selectSettingsLoadState = createSelector(
  selectSettings,
  ({ loading, error }): LoadSourceState => ({ loading, errorKey: error })
)

export const selectMapLayersLoadState = createSelector(
  (state: RootState) => state.mapLayers,
  ({ pendingLoads, latestErrorVersion }): LoadSourceState => ({
    loading: pendingLoads > 0,
    errorKey: latestErrorVersion > 0 ? String(latestErrorVersion) : null
  })
)

export type NotificationSetupState = 'permissionDenied' | 'unregistered' | 'registrationFailed' | 'ready'

export const selectNotificationSetupState = createSelector(
  selectPushNotification,
  ({ pushNotificationPermission, registeredFcmToken, registrationError }): NotificationSetupState => {
    if (pushNotificationPermission !== 'granted') {
      return 'permissionDenied'
    }
    if (!registeredFcmToken) {
      return registrationError ? 'registrationFailed' : 'unregistered'
    }
    return 'ready'
  }
)

export const selectRegistrationFailed = createSelector(
  selectNotificationSetupState,
  setupState => setupState === 'registrationFailed'
)

export const selectNotificationSettingsDisabled = createSelector(
  selectNotificationSetupState,
  selectNetworkStatus,
  selectSettings,
  (setupState, { networkStatus }, { subscriptionsInitialized }) =>
    setupState !== 'ready' || !networkStatus.connected || !subscriptionsInitialized
)
