import { type Action, configureStore, createSelector, type ThunkAction } from '@reduxjs/toolkit'
import { rootReducer } from '@/rootReducer'
import { getNotificationPriority } from '@/slices/notificationSlice'
import type { LoadError } from '@/utils/loadError'

export const store = configureStore({
  reducer: rootReducer
})

// Infer the `RootState` and `AppDispatch` types from the store itself
export type RootState = ReturnType<typeof store.getState>
// Inferred type: {posts: PostsState, comments: CommentsState, users: UsersState}
export type AppDispatch = typeof store.dispatch

// allow async thunks to expose their promise when callers need to await nested work
export type AppThunk<ReturnType = void> = ThunkAction<ReturnType, RootState, undefined, Action>

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

export interface ActiveLoadError {
  error: LoadError
  source: 'operational' | 'settings'
}

export const selectOperationalDataLoading = createSelector(
  [
    (state: RootState) => state.fireCentres,
    (state: RootState) => state.runParameters,
    (state: RootState) => state.data
  ],
  (fireCentres, runParameters, data) => {
    const operationalDataUnavailable =
      data.provincialSummaries === null || data.tpiStats === null || data.hfiStats === null

    // run parameter refreshes are background checks. show loading only while operational data is still missing
    return fireCentres.loading || data.loading || (runParameters.loading && operationalDataUnavailable)
  }
)

export const selectActiveLoadError = createSelector(
  [
    (state: RootState) => state.settings.error,
    (state: RootState) => state.data.error,
    (state: RootState) => state.fireCentres.error,
    (state: RootState) => state.runParameters.error
  ],
  (settingsError, dataError, fireCentresError, runParametersError): ActiveLoadError | null => {
    if (settingsError) return { error: settingsError, source: 'settings' }

    const operationalError = dataError ?? fireCentresError ?? runParametersError
    if (!operationalError) return null

    return { error: operationalError, source: 'operational' }
  }
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
