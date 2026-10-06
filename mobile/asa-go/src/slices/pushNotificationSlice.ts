import { Capacitor, type PermissionState } from '@capacitor/core'
import { Device } from '@capacitor/device'
import { FirebaseMessaging } from '@capacitor-firebase/messaging'
import { createSlice, type PayloadAction } from '@reduxjs/toolkit'
import { type Platform, registerToken } from 'api/pushNotificationsAPI'
import type { AppThunk } from '@/store'
import type { PushNotificationData } from '@/types/asaGoTypes'
import { retryWithBackoff } from '@/utils/retryWithBackoff'

export interface PushNotificationState {
  pushNotificationPermission: PermissionState | 'unknown'
  registeredFcmToken: string | null
  deviceIdError: boolean
  registrationError: boolean
  pendingNotificationData: PushNotificationData | null
}

export const initialState: PushNotificationState = {
  pushNotificationPermission: 'unknown',
  registeredFcmToken: null,
  deviceIdError: false,
  registrationError: false,
  pendingNotificationData: null
}

const pushNotificationSlice = createSlice({
  name: 'pushNotification',
  initialState,
  reducers: {
    setPushNotificationPermission(state: PushNotificationState, action: PayloadAction<PermissionState | 'unknown'>) {
      state.pushNotificationPermission = action.payload
    },
    setRegisteredFcmToken(state: PushNotificationState, action: PayloadAction<string | null>) {
      state.registeredFcmToken = action.payload
    },
    setDeviceIdError(state: PushNotificationState, action: PayloadAction<boolean>) {
      state.deviceIdError = action.payload
    },
    setRegistrationError(state: PushNotificationState, action: PayloadAction<boolean>) {
      state.registrationError = action.payload
    },
    setPendingNotificationData(state: PushNotificationState, action: PayloadAction<PushNotificationData>) {
      state.pendingNotificationData = action.payload
    },
    clearPendingNotificationData(state: PushNotificationState) {
      state.pendingNotificationData = null
    }
  }
})

export const {
  setDeviceIdError,
  setRegistrationError,
  setPushNotificationPermission,
  setRegisteredFcmToken,
  setPendingNotificationData,
  clearPendingNotificationData
} = pushNotificationSlice.actions

export default pushNotificationSlice.reducer

export const checkPushNotificationPermission = (): AppThunk<Promise<void>> => async dispatch => {
  try {
    const permissions = await FirebaseMessaging.checkPermissions()
    dispatch(setPushNotificationPermission(permissions.receive ?? 'unknown'))
  } catch (e) {
    console.error(e)
    dispatch(setPushNotificationPermission('unknown'))
  }
}

export const registerDevice =
  (token: string, registeredFcmToken: string | null): AppThunk<Promise<void>> =>
  async (dispatch, getState) => {
    if (token === registeredFcmToken) return
    try {
      const { idir } = getState().authentication
      const { identifier } = await Device.getId()
      await retryWithBackoff(() => registerToken(Capacitor.getPlatform() as Platform, token, identifier, idir || null))
      dispatch(setRegistrationError(false))
      dispatch(setRegisteredFcmToken(token))
    } catch (e) {
      console.error('Failed to register device:', e)
      dispatch(setRegistrationError(true))
    }
  }

export const retryPushNotificationRegistration = (): AppThunk<Promise<void>> => async (dispatch, getState) => {
  const { registeredFcmToken, registrationError } = getState().pushNotification
  if (!registrationError) return

  try {
    const { token } = await FirebaseMessaging.getToken()
    // wait so retry completion reflects the final registration state
    if (token) await dispatch(registerDevice(token, registeredFcmToken))
  } catch (e) {
    console.error('Failed to get token for retry:', e)
    dispatch(setRegistrationError(true))
  }
}
