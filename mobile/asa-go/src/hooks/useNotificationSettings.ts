import {
  getNotificationSettings,
  registerToken,
  updateNotificationSettings,
} from "api/pushNotificationsAPI";
import { Capacitor } from "@capacitor/core";
import { Device } from "@capacitor/device";
import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  getUpdatedSubscriptions,
  saveSubscriptions,
  setDeviceIdError,
  setSubscriptions,
  setTokenRegistered,
} from "@/slices/settingsSlice";
import { AppDispatch, selectAuthentication, selectNetworkStatus, selectSettings } from "@/store";
import { Platform } from "api/pushNotificationsAPI";

export function useNotificationSettings() {
  const dispatch = useDispatch<AppDispatch>();
  const { networkStatus } = useSelector(selectNetworkStatus);
  const { subscriptions, tokenRegistered, fcmToken } = useSelector(selectSettings);
  const { idir } = useSelector(selectAuthentication);
  const [deviceId, setDeviceId] = useState<string | null>(null);

  useEffect(() => {
    Device.getId()
      .then((info) => {
        setDeviceId(info.identifier);
        dispatch(setDeviceIdError(false));
      })
      .catch((e) => {
        console.error(`Failed to get device ID: ${e}`);
        dispatch(setDeviceIdError(true));
      });
  }, [dispatch]);

  // Fetch from server once registered, and again when coming back online
  useEffect(() => {
    if (!deviceId || !networkStatus.connected || !tokenRegistered) return;
    getNotificationSettings(deviceId)
      .then((ids) => {
        const subs = ids.map(Number);
        dispatch(setSubscriptions(subs));
      })
      .catch((e) =>
        console.error(`Failed to fetch notification settings: ${e}`),
      );
  }, [deviceId, networkStatus.connected, tokenRegistered, dispatch]);

  const ensureRegistered = async (): Promise<boolean> => {
    if (tokenRegistered) return true;
    if (!fcmToken || !deviceId) return false;
    try {
      await registerToken(Capacitor.getPlatform() as Platform, fcmToken, deviceId, idir || null);
      dispatch(setTokenRegistered(true));
      return true;
    } catch (e) {
      console.error(`Failed to register device: ${e}`);
      return false;
    }
  };

  const updateSubscriptions = async (subs: number[]) => {
    const previousSubs = subscriptions;
    dispatch(saveSubscriptions(subs));
    if (!deviceId || !networkStatus.connected) {
      dispatch(saveSubscriptions(previousSubs));
      return;
    }
    if (!await ensureRegistered()) {
      dispatch(saveSubscriptions(previousSubs));
      return;
    }
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
