import { AppThunk } from "@/store";
import { PushNotificationData } from "@/types/asaGoTypes";
import { retryWithBackoff } from "@/utils/retryWithBackoff";
import { FirebaseMessaging } from "@capacitor-firebase/messaging";
import { Capacitor, PermissionState } from "@capacitor/core";
import { Device } from "@capacitor/device";
import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { Platform, registerToken } from "api/pushNotificationsAPI";

export const MAX_REGISTRATION_ATTEMPTS = 5;

export interface PushNotificationState {
  pushNotificationPermission: PermissionState | "unknown";
  registeredFcmToken: string | null;
  deviceIdError: boolean;
  registrationError: boolean;
  registrationAttempts: number;
  pendingNotificationData: PushNotificationData | null;
}

export const initialState: PushNotificationState = {
  pushNotificationPermission: "unknown",
  registeredFcmToken: null,
  deviceIdError: false,
  registrationError: false,
  registrationAttempts: 0,
  pendingNotificationData: null,
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
    setDeviceIdError(
      state: PushNotificationState,
      action: PayloadAction<boolean>,
    ) {
      state.deviceIdError = action.payload;
    },
    setRegistrationError(
      state: PushNotificationState,
      action: PayloadAction<boolean>,
    ) {
      state.registrationError = action.payload;
    },
    incrementRegistrationAttempts(state: PushNotificationState) {
      state.registrationAttempts += 1;
    },
    resetRegistrationAttempts(state: PushNotificationState) {
      state.registrationAttempts = 0;
    },
    setPendingNotificationData(
      state: PushNotificationState,
      action: PayloadAction<PushNotificationData>,
    ) {
      state.pendingNotificationData = action.payload;
    },
    clearPendingNotificationData(state: PushNotificationState) {
      state.pendingNotificationData = null;
    },
  },
});

export const {
  setDeviceIdError,
  setRegistrationError,
  setPushNotificationPermission,
  setRegisteredFcmToken,
  incrementRegistrationAttempts,
  resetRegistrationAttempts,
  setPendingNotificationData,
  clearPendingNotificationData,
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
  (token: string, registeredFcmToken: string | null): AppThunk =>
  async (dispatch, getState) => {
    if (token === registeredFcmToken) return;
    try {
      const { idir } = getState().authentication;
      const { identifier } = await Device.getId();
      await retryWithBackoff(() =>
        registerToken(
          Capacitor.getPlatform() as Platform,
          token,
          identifier,
          idir || null,
        ),
      );
      dispatch(setRegistrationError(false));
      dispatch(resetRegistrationAttempts());
      dispatch(setRegisteredFcmToken(token));
    } catch (e) {
      console.error("Failed to register device:", e);
      dispatch(incrementRegistrationAttempts());
      dispatch(setRegistrationError(true));
    }
  };
