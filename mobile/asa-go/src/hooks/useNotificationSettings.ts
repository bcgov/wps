import { updateNotificationSettings } from 'api/pushNotificationsAPI'
import { useDispatch, useSelector } from 'react-redux'
import { useDeviceId } from '@/hooks/useDeviceId'
import { enqueueNotification } from '@/slices/notificationSlice'
import { setSubscriptions } from '@/slices/settingsSlice'
import { type AppDispatch, selectNetworkStatus, selectPushNotification, selectSettings } from '@/store'
import { subscriptionUpdateErrorMessage } from '@/utils/constants'
import { retryWithBackoff } from '@/utils/retryWithBackoff'
import { getUpdatedSubscriptions } from '@/utils/subscriptionUtils'

export function useNotificationSettings() {
  const dispatch = useDispatch<AppDispatch>()
  const { networkStatus } = useSelector(selectNetworkStatus)
  const { subscriptions } = useSelector(selectSettings)
  const { registeredFcmToken } = useSelector(selectPushNotification)
  const { subscriptionsInitialized } = useSelector(selectSettings)
  const deviceId = useDeviceId()

  const updateSubscriptions = async (subs: number[]): Promise<boolean> => {
    // Guard matches selectNotificationSettingsDisabled — button should be disabled
    // before this is reachable, but guard prevents any state change if not.
    if (!deviceId || !networkStatus.connected || !registeredFcmToken || !subscriptionsInitialized) return false
    const previousSubs = subscriptions
    dispatch(setSubscriptions(subs))
    try {
      const ids = await retryWithBackoff(() => updateNotificationSettings(deviceId, subs.map(String)))
      dispatch(setSubscriptions(ids.map(Number)))
      return true
    } catch (e) {
      console.error(`Failed to update notification settings: ${e}`)
      dispatch(setSubscriptions(previousSubs))
      dispatch(
        enqueueNotification({
          dedupeKey: 'subscription-update-error',
          message: subscriptionUpdateErrorMessage,
          severity: 'error'
        })
      )
      return false
    }
  }

  const toggleSubscription = (fireZoneUnitId: number) =>
    updateSubscriptions(getUpdatedSubscriptions(subscriptions, fireZoneUnitId))

  return {
    updateSubscriptions,
    toggleSubscription
  }
}
