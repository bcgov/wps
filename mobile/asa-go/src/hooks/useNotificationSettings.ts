import { updateNotificationSettings } from "api/pushNotificationsAPI";
import { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  getUpdatedSubscriptions,
  setSubscriptions,
} from "@/slices/settingsSlice";
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
  const deviceId = useDeviceId();
  const [updateError, setUpdateError] = useState(false);

  const updateSubscriptions = async (subs: number[]): Promise<void> => {
    // Guard matches selectNotificationSettingsDisabled — button should be disabled
    // before this is reachable, but guard prevents any state change if not.
    if (!deviceId || !networkStatus.connected || !registeredFcmToken) return;
    const previousSubs = subscriptions;
    dispatch(setSubscriptions(subs));
    try {
      const ids = await retryWithBackoff(() =>
        updateNotificationSettings(deviceId, subs.map(String)),
      );
      dispatch(setSubscriptions(ids.map(Number)));
      setUpdateError(false);
    } catch (e) {
      console.error(`Failed to update notification settings: ${e}`);
      dispatch(setSubscriptions(previousSubs));
      setUpdateError(true);
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
