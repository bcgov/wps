import CancelOutlinedIcon from '@mui/icons-material/CancelOutlined'
import { useEffect, useRef } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import NotificationSnackbar from '@/components/NotificationSnackbar'
import { dismissNotification, enqueueNotification, removeNotificationByKey } from '@/slices/notificationSlice'
import { type AppDispatch, selectCurrentNotification, selectNetworkStatus, selectRegistrationFailed } from '@/store'

const REGISTRATION_ERROR_NOTIFICATION_KEY = 'push-registration-error'
const REGISTRATION_ERROR_MESSAGE = 'Unable to register this device for notifications. Retrying automatically.'

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
      dispatch(
        enqueueNotification({
          autoHideDuration: null,
          dedupeKey: REGISTRATION_ERROR_NOTIFICATION_KEY,
          message: REGISTRATION_ERROR_MESSAGE,
          severity: 'warning'
        })
      )
    } else if (!shouldShowRegistrationError && registrationFailureActive.current) {
      registrationFailureActive.current = false
      dispatch(removeNotificationByKey(REGISTRATION_ERROR_NOTIFICATION_KEY))
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
