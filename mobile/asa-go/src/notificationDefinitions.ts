import type { EnqueueNotificationPayload } from '@/slices/notificationSlice'

const LOADING_ERROR_NOTIFICATION_KEY = 'loading-error'

export const NOTIFICATION_DEFINITIONS = {
  feedbackSuccess: {
    autoHideDuration: 4000,
    dedupeKey: 'feedback-success',
    message: 'Thank you for your feedback.',
    severity: 'success'
  },
  hfiCacheError: {
    dedupeKey: 'hfi-cache-error',
    message: 'Unable to update HFI map data. Some map information may be unavailable.',
    severity: 'error'
  },
  operationalDataError: {
    dedupeKey: LOADING_ERROR_NOTIFICATION_KEY,
    message: 'Unable to update operational data. Displayed data may be stale.',
    severity: 'error'
  },
  pushRegistrationError: {
    autoHideDuration: null,
    dedupeKey: 'push-registration-error',
    message: 'Unable to register this device for notifications.',
    severity: 'warning'
  },
  settingsDataError: {
    dedupeKey: LOADING_ERROR_NOTIFICATION_KEY,
    message: 'Unable to load notification settings. Check your connection and try again.',
    severity: 'error'
  },
  subscriptionUpdateError: {
    dedupeKey: 'subscription-update-error',
    message: 'Failed to update notification settings. Please try again later.',
    severity: 'error'
  }
} as const satisfies Record<string, EnqueueNotificationPayload>

export const withHttpStatus = (notification: EnqueueNotificationPayload, status?: number) => ({
  ...notification,
  message: status === undefined ? notification.message : `${status} Error - ${notification.message}`
})
