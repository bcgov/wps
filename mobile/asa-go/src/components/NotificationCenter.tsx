import CancelOutlinedIcon from '@mui/icons-material/CancelOutlined'
import { useEffect, useRef } from 'react'
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
  const registrationFailureActive = useRef(false)
  const shouldShowRegistrationError = isRegistrationFailed && networkStatus.connected

  useEffect(() => {
    if (shouldShowRegistrationError && !registrationFailureActive.current) {
      registrationFailureActive.current = true
      dispatch(enqueueNotification(NOTIFICATION_DEFINITIONS.pushRegistrationError))
    } else if (!shouldShowRegistrationError && registrationFailureActive.current) {
      registrationFailureActive.current = false
      dispatch(removeNotificationByKey(NOTIFICATION_DEFINITIONS.pushRegistrationError.dedupeKey))
    }
  }, [dispatch, shouldShowRegistrationError])

  if (!notification) return null

  return (
    <NotificationSnackbar
      key={notification.id}
      autoHideDuration={notification.autoHideDuration}
      icon={notification.severity === 'error' ? <CancelOutlinedIcon sx={{ color: 'error.dark' }} /> : undefined}
      message={notification.message}
      onClose={() => dispatch(dismissNotification(notification.id))}
      open
      severity={notification.severity}
      testId="notification-center"
    />
  )
}

export default NotificationCenter
