import { useEffect, useRef } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { enqueueNotification, removeNotificationByKey } from '@/slices/notificationSlice'
import { type AppDispatch, type RootState, selectOperationalLoadState, selectSettingsLoadState } from '@/store'

const OPERATIONAL_DATA_ERROR_MESSAGE = 'Unable to update operational data. Displayed data may be stale.'
const SETTINGS_DATA_ERROR_MESSAGE = 'Unable to load notification settings. Check your connection and try again.'

const LOADING_ERROR_NOTIFICATION_KEY = 'loading-error'

interface LoadingErrorKeys {
  operational: string | null
  settings: string | null
}

const getErrorMessage = (operationalErrorPending: boolean, settingsErrorPending: boolean) => {
  if (settingsErrorPending) return SETTINGS_DATA_ERROR_MESSAGE
  if (operationalErrorPending) return OPERATIONAL_DATA_ERROR_MESSAGE
  return null
}

// reset resolved errors and remember occurrences already shown or covered by the offline banner
const getHandledErrorKey = (errorKey: string | null, handledErrorKey: string | null, shouldMarkHandled: boolean) =>
  errorKey === null || shouldMarkHandled ? errorKey : handledErrorKey

const LoadingErrorNotifier = () => {
  const dispatch: AppDispatch = useDispatch()
  const connected = useSelector((state: RootState) => state.networkStatus.networkStatus.connected)
  const { errorKey: operationalError } = useSelector(selectOperationalLoadState)
  const { errorKey: settingsError } = useSelector(selectSettingsLoadState)
  // source errors outlive dismissed notifications, so remember which occurrences were already handled
  const handledErrorKeys = useRef<LoadingErrorKeys>({ operational: null, settings: null })

  useEffect(() => {
    const operationalErrorPending =
      connected && operationalError !== null && operationalError !== handledErrorKeys.current.operational
    const settingsErrorPending =
      connected && settingsError !== null && settingsError !== handledErrorKeys.current.settings
    const message = getErrorMessage(operationalErrorPending, settingsErrorPending)

    handledErrorKeys.current = {
      // offline API failures are handled by the persistent InfoBar instead of a notification
      operational: getHandledErrorKey(
        operationalError,
        handledErrorKeys.current.operational,
        operationalErrorPending || !connected
      ),
      settings: getHandledErrorKey(settingsError, handledErrorKeys.current.settings, settingsErrorPending || !connected)
    }

    const notificationAction = message
      ? enqueueNotification({
          dedupeKey: LOADING_ERROR_NOTIFICATION_KEY,
          message,
          severity: 'error'
        })
      : removeNotificationByKey(LOADING_ERROR_NOTIFICATION_KEY)

    dispatch(notificationAction)
  }, [connected, dispatch, operationalError, settingsError])

  return null
}

export default LoadingErrorNotifier
