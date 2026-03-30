import { AppThunk } from "@/store";
import { retryWithBackoff } from "@/utils/retryWithBackoff";
import { FirebaseMessaging } from "@capacitor-firebase/messaging";
import { Capacitor, PermissionState } from "@capacitor/core";
import { Device } from "@capacitor/device";
import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { Platform, registerToken } from "api/pushNotificationsAPI";

export interface PushNotificationState {
  pushNotificationPermission: PermissionState | "unknown";
  registeredFcmToken: string | null;
  deviceIdError: boolean;
}

export const initialState: PushNotificationState = {
  pushNotificationPermission: "unknown",
  registeredFcmToken: null,
  deviceIdError: false,
};

const pushNotificationSlice = createSlice({
  name: "pushNotification",
  initialState,
  reducers: {
    setPushNotificationPermission(
      state: PushNotificationState,
      action: PayloadAction<PermissionState | "unknown">,
    ) {
      state.pushNotificationPermission = action.payload;
    },
    setRegisteredFcmToken(
      state: PushNotificationState,
      action: PayloadAction<string | null>,
    ) {
      state.registeredFcmToken = action.payload;
    },
    setDeviceIdError(state: PushNotificationState, action: PayloadAction<boolean>) {
      state.deviceIdError = action.payload;
    },
  },
});

export const {
  setDeviceIdError,
  setPushNotificationPermission,
  setRegisteredFcmToken,
} = pushNotificationSlice.actions;

export default pushNotificationSlice.reducer;

export const checkPushNotificationPermission =
  (): AppThunk => async (dispatch) => {
    try {
      const permissions = await FirebaseMessaging.checkPermissions();
      dispatch(setPushNotificationPermission(permissions.receive ?? "unknown"));
    } catch (e) {
      console.error(e);
      dispatch(setPushNotificationPermission("unknown"));
    }
  };

export const registerDevice =
  (registeredFcmToken: string | null): AppThunk =>
  async (dispatch, getState) => {
    try {
      const { token } = await FirebaseMessaging.getToken();
      if (!token) return; // no token available yet
      if (token === registeredFcmToken) return; // already registered, nothing to do
      const { idir } = getState().authentication;
      const { identifier } = await Device.getId();
      await retryWithBackoff(() =>
        registerToken(Capacitor.getPlatform() as Platform, token, identifier, idir || null),
      );
      dispatch(setRegisteredFcmToken(token));
    } catch (e) {
      console.error("Failed to register device:", e);
    }
  };
