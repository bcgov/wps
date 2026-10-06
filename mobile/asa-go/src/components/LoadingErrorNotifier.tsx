import { useEffect, useRef } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { NOTIFICATION_DEFINITIONS } from '@/notificationDefinitions'
import { enqueueNotification, removeNotificationByKey } from '@/slices/notificationSlice'
import { type AppDispatch, type RootState, selectOperationalLoadState, selectSettingsLoadState } from '@/store'

interface LoadingErrorKeys {
  operational: string | null
  settings: string | null
}

const getErrorNotification = (operationalErrorPending: boolean, settingsErrorPending: boolean) => {
  if (settingsErrorPending) return NOTIFICATION_DEFINITIONS.settingsDataError
  if (operationalErrorPending) return NOTIFICATION_DEFINITIONS.operationalDataError
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
    const notification = getErrorNotification(operationalErrorPending, settingsErrorPending)

    handledErrorKeys.current = {
      // offline API failures are handled by the persistent InfoBar instead of a notification
      operational: getHandledErrorKey(
        operationalError,
        handledErrorKeys.current.operational,
        operationalErrorPending || !connected
      ),
      settings: getHandledErrorKey(settingsError, handledErrorKeys.current.settings, settingsErrorPending || !connected)
    }

    const notificationAction = notification
      ? enqueueNotification(notification)
      : removeNotificationByKey(NOTIFICATION_DEFINITIONS.operationalDataError.dedupeKey)

    dispatch(notificationAction)
  }, [connected, dispatch, operationalError, settingsError])

  return null
}

export default LoadingErrorNotifier
