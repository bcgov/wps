import {
  getNotificationSettings,
  updateNotificationSettings,
} from "api/pushNotificationsAPI";
import { Device } from "@capacitor/device";
import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  getUpdatedSubscriptions,
  saveSubscriptions,
  setSubscriptions,
} from "@/slices/settingsSlice";
import { AppDispatch, selectNetworkStatus, selectSettings } from "@/store";

export function useNotificationSettings() {
  const dispatch = useDispatch<AppDispatch>();
  const { networkStatus } = useSelector(selectNetworkStatus);
  const { subscriptions } = useSelector(selectSettings);
  const [deviceId, setDeviceId] = useState<string | null>(null);

  useEffect(() => {
    Device.getId()
      .then((info) => setDeviceId(info.identifier))
      .catch((e) => console.error(`Failed to get device ID: ${e}`));
  }, []);

  // Fetch from server on mount and when coming online
  useEffect(() => {
    if (!deviceId || !networkStatus.connected) return;
    getNotificationSettings(deviceId)
      .then((ids) => {
        const subs = ids.map(Number);
        dispatch(setSubscriptions(subs));
      })
      .catch((e) =>
        console.error(`Failed to fetch notification settings: ${e}`),
      );
  }, [deviceId, networkStatus.connected, dispatch]);

  const updateSubscriptions = async (subs: number[]) => {
    const previousSubs = subscriptions;
    dispatch(saveSubscriptions(subs));
    if (!deviceId || !networkStatus.connected) return;
    try {
      const fireZoneSourceIds = await updateNotificationSettings(
        deviceId,
        subs.map(String),
      );
      dispatch(setSubscriptions(fireZoneSourceIds.map(Number)));
    } catch (e) {
      console.error(`Failed to update notification settings: ${e}`);
      dispatch(saveSubscriptions(previousSubs));
    }
  };

  const toggleSubscription = (fireZoneUnitId: number) =>
    updateSubscriptions(getUpdatedSubscriptions(subscriptions, fireZoneUnitId));

  return { updateSubscriptions, toggleSubscription };
}
