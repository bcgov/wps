import {
  getNotificationSettings,
  updateNotificationSettings,
} from "api/pushNotificationsAPI";
import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  getUpdatedSubscriptions,
  setSubscriptions,
} from "@/slices/settingsSlice";
import { AppDispatch, selectNetworkStatus, selectPushNotification, selectSettings } from "@/store";
import { useDeviceId } from "@/hooks/useDeviceId";
import { retryWithBackoff } from "@/utils/retryWithBackoff";

export function useNotificationSettings() {
  const dispatch = useDispatch<AppDispatch>();
  const { networkStatus } = useSelector(selectNetworkStatus);
  const { subscriptions } = useSelector(selectSettings);
  const { registeredFcmToken } = useSelector(selectPushNotification);
  const deviceId = useDeviceId();
  const [updateError, setUpdateError] = useState(false);

  // Fetch from server once registered, and again when coming back online.
  // The guard is intentional: deviceId and registeredFcmToken resolve asynchronously
  // after mount, and networkStatus may start offline. The effect re-runs automatically
  // when any dependency changes, so no fetch is missed.
  useEffect(() => {
    if (!deviceId || !networkStatus.connected || !registeredFcmToken) return;
    getNotificationSettings(deviceId)
      .then((ids) => dispatch(setSubscriptions(ids.map(Number))))
      .catch((e) => console.error(`Failed to fetch notification settings: ${e}`));
  }, [deviceId, networkStatus.connected, registeredFcmToken, dispatch]);

  const updateSubscriptions = async (subs: number[]) => {
    // Guard matches selectNotificationSettingsDisabled — button should be disabled
    // before this is reachable, but guard prevents any state change if not.
    if (!deviceId || !networkStatus.connected || !registeredFcmToken) return;
    const previousSubs = subscriptions;
    dispatch(setSubscriptions(subs));
    retryWithBackoff(() => updateNotificationSettings(deviceId, subs.map(String)))
      .then((ids) => {
        dispatch(setSubscriptions(ids.map(Number)));
        setUpdateError(false);
      })
      .catch((e) => {
        console.error(`Failed to update notification settings: ${e}`);
        dispatch(setSubscriptions(previousSubs));
        setUpdateError(true);
      });
  };

  const toggleSubscription = (fireZoneUnitId: number) =>
    updateSubscriptions(getUpdatedSubscriptions(subscriptions, fireZoneUnitId));

  return { updateSubscriptions, toggleSubscription, updateError };
}
