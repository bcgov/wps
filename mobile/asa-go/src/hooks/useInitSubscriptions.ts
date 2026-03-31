import { getNotificationSettings } from "api/pushNotificationsAPI";
import { useEffect } from "react";
import { useDispatch, useSelector, useStore } from "react-redux";
import { setSubscriptions } from "@/slices/settingsSlice";
import { AppDispatch, RootState, selectNetworkStatus, selectPushNotification, selectSettings } from "@/store";
import { useDeviceId } from "@/hooks/useDeviceId";
import { retryWithBackoff } from "@/utils/retryWithBackoff";

export function useInitSubscriptions() {
  const dispatch = useDispatch<AppDispatch>();
  const store = useStore<RootState>();
  const { networkStatus } = useSelector(selectNetworkStatus);
  const { registeredFcmToken } = useSelector(selectPushNotification);
  const { subscriptionsInitialized } = useSelector(selectSettings);
  const deviceId = useDeviceId();

  // Fetch subscriptions from the server once on first load.
  // subscriptionsInitialized is read from store.getState() inside the callback
  // (not from the selector closure) so it reflects synchronous dispatches that
  // happened while the fetch was in-flight, before React has had a chance to
  // re-render and run effect cleanup.
  useEffect(() => {
    if (!deviceId || !networkStatus.connected || !registeredFcmToken) return;
    if (subscriptionsInitialized) return;
    retryWithBackoff(() => getNotificationSettings(deviceId))
      .then((ids) => {
        if (!store.getState().settings.subscriptionsInitialized) {
          dispatch(setSubscriptions(ids.map(Number)));
        }
      })
      .catch((e) => console.error(`Failed to fetch notification settings: ${e}`));
  }, [deviceId, networkStatus.connected, registeredFcmToken, subscriptionsInitialized, dispatch, store]);
}
