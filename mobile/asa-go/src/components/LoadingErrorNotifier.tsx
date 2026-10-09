import { useEffect, useRef } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { NOTIFICATION_DEFINITIONS, withHttpStatus } from '@/notificationDefinitions'
import { enqueueNotification, removeNotificationByKey } from '@/slices/notificationSlice'
import { type AppDispatch, type RootState, selectActiveLoadError } from '@/store'

const ERROR_NOTIFICATIONS = {
  operational: NOTIFICATION_DEFINITIONS.operationalDataError,
  settings: NOTIFICATION_DEFINITIONS.settingsDataError
}

const LoadingErrorNotifier = () => {
  const dispatch: AppDispatch = useDispatch()
  const connected = useSelector((state: RootState) => state.networkStatus.networkStatus.connected)
  const activeError = useSelector(selectActiveLoadError)
  // remember the current error so dismissed and offline notifications stay closed
  const handledErrorKey = useRef<string | null>(null)

  useEffect(() => {
    if (!activeError) {
      handledErrorKey.current = null
      dispatch(removeNotificationByKey(NOTIFICATION_DEFINITIONS.operationalDataError.dedupeKey))
      return
    }

    const currentErrorKey = `${activeError.source}:${activeError.error.key}`
    if (!connected) {
      handledErrorKey.current = currentErrorKey
      dispatch(removeNotificationByKey(NOTIFICATION_DEFINITIONS.operationalDataError.dedupeKey))
      return
    }

    if (handledErrorKey.current === currentErrorKey) return

    handledErrorKey.current = currentErrorKey
    const notification = withHttpStatus(ERROR_NOTIFICATIONS[activeError.source], activeError.error.status)
    dispatch(enqueueNotification(notification))
  }, [activeError, connected, dispatch])

  return null
}

export default LoadingErrorNotifier
