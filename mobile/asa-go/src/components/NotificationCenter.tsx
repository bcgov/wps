import CancelOutlinedIcon from '@mui/icons-material/CancelOutlined'
import { useCallback, useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import NotificationSnackbar from '@/components/NotificationSnackbar'
import { NOTIFICATION_DEFINITIONS } from '@/notificationDefinitions'
import { dismissNotification, enqueueNotification, removeNotificationByKey } from '@/slices/notificationSlice'
import { type AppDispatch, selectCurrentNotification, selectNetworkStatus, selectRegistrationFailed } from '@/store'

const NotificationCenter = () => {
  const dispatch: AppDispatch = useDispatch()
  const notification = useSelector(selectCurrentNotification)
  const isRegistrationFailed = useSelector(selectRegistrationFailed)
  const { networkStatus } = useSelector(selectNetworkStatus)
  const shouldShowRegistrationError = isRegistrationFailed && networkStatus.connected
  const notificationId = notification?.id

  const handleClose = useCallback(() => {
    if (notificationId) dispatch(dismissNotification(notificationId))
  }, [dispatch, notificationId])

  useEffect(() => {
    const action = shouldShowRegistrationError
      ? enqueueNotification(NOTIFICATION_DEFINITIONS.pushRegistrationError)
      : removeNotificationByKey(NOTIFICATION_DEFINITIONS.pushRegistrationError.dedupeKey)
    dispatch(action)
  }, [dispatch, shouldShowRegistrationError])

  if (!notification) return null

  return (
    <NotificationSnackbar
      key={notification.id}
      autoHideDuration={notification.autoHideDuration}
      icon={notification.severity === 'error' ? <CancelOutlinedIcon sx={{ color: 'error.dark' }} /> : undefined}
      message={notification.message}
      onClose={handleClose}
      open
      severity={notification.severity}
      testId="notification-center"
    />
  )
}

export default NotificationCenter
