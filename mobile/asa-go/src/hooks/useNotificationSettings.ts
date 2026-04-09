import { updateNotificationSettings } from "api/pushNotificationsAPI";
import { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { setSubscriptions } from "@/slices/settingsSlice";
import { getUpdatedSubscriptions } from "@/utils/subscriptionUtils";
import {
  AppDispatch,
  selectNetworkStatus,
  selectPushNotification,
  selectSettings,
} from "@/store";
import { useDeviceId } from "@/hooks/useDeviceId";
import { retryWithBackoff } from "@/utils/retryWithBackoff";

export function useNotificationSettings() {
  const dispatch = useDispatch<AppDispatch>();
  const { networkStatus } = useSelector(selectNetworkStatus);
  const { subscriptions } = useSelector(selectSettings);
  const { registeredFcmToken } = useSelector(selectPushNotification);
  const { subscriptionsInitialized } = useSelector(selectSettings);
  const deviceId = useDeviceId();
  const [updateError, setUpdateError] = useState(false);

  const updateSubscriptions = async (subs: number[]): Promise<boolean> => {
    // Guard matches selectNotificationSettingsDisabled — button should be disabled
    // before this is reachable, but guard prevents any state change if not.
    if (
      !deviceId ||
      !networkStatus.connected ||
      !registeredFcmToken ||
      !subscriptionsInitialized
    )
      return false;
    const previousSubs = subscriptions;
    dispatch(setSubscriptions(subs));
    try {
      const ids = await retryWithBackoff(() =>
        updateNotificationSettings(deviceId, subs.map(String)),
      );
      dispatch(setSubscriptions(ids.map(Number)));
      setUpdateError(false);
      return true;
    } catch (e) {
      console.error(`Failed to update notification settings: ${e}`);
      dispatch(setSubscriptions(previousSubs));
      setUpdateError(true);
      return false;
    }
  };

  const toggleSubscription = (fireZoneUnitId: number) =>
    updateSubscriptions(getUpdatedSubscriptions(subscriptions, fireZoneUnitId));

  const clearUpdateError = () => setUpdateError(false);

  return {
    updateSubscriptions,
    toggleSubscription,
    updateError,
    clearUpdateError,
  };
}
