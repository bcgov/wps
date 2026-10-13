import { Capacitor, type PluginListenerHandle } from '@capacitor/core'
import { type ActionPerformed, LocalNotifications } from '@capacitor/local-notifications'
import {
  FirebaseMessaging,
  Importance,
  type NotificationActionPerformedEvent,
  type NotificationReceivedEvent,
  type PermissionStatus,
  type TokenReceivedEvent
} from '@capacitor-firebase/messaging'
import { useCallback, useEffect, useRef, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { useAppIsActive } from '@/hooks/useAppIsActive'
import {
  registerDevice,
  retryPushNotificationRegistration,
  setPendingNotificationData,
  setPushNotificationPermission,
  setRegistrationError
} from '@/slices/pushNotificationSlice'
import { type AppDispatch, selectNetworkStatus, selectPushNotification } from '@/store'
import type { PushNotificationData } from '@/types/asaGoTypes'

const ANDROID_CHANNEL = {
  id: 'general',
  name: 'General',
  description: 'General notifications',
  importance: Importance.High,
  sound: 'default'
}

export function usePushNotifications() {
  const [currentFcmToken, setCurrentFcmToken] = useState<string | null>(null)
  const handles = useRef<PluginListenerHandle[]>([])
  const initialized = useRef(false)
  const dispatch = useDispatch<AppDispatch>()
  const { registeredFcmToken } = useSelector(selectPushNotification)
  const { networkStatus } = useSelector(selectNetworkStatus)
  const isActive = useAppIsActive()

  const initPushNotifications = useCallback(async () => {
    if (initialized.current) return
    try {
      const check: PermissionStatus = await FirebaseMessaging.checkPermissions()
      dispatch(setPushNotificationPermission(check.receive ?? 'unknown'))
      if (check.receive !== 'granted') {
        const req = await FirebaseMessaging.requestPermissions()
        dispatch(setPushNotificationPermission(req.receive ?? 'unknown'))
        if (req.receive !== 'granted') return
      }

      if (Capacitor.getPlatform() === 'android') {
        await FirebaseMessaging.createChannel(ANDROID_CHANNEL)
      }

      try {
        const { token } = await FirebaseMessaging.getToken()
        setCurrentFcmToken(token)
      } catch (e) {
        console.error('Failed to get FCM token during init:', e)
        dispatch(setRegistrationError(true))
        return
      }

      const tokenHandle = await FirebaseMessaging.addListener('tokenReceived', (e: TokenReceivedEvent) =>
        setCurrentFcmToken(e.token)
      )

      const receivedHandle = await FirebaseMessaging.addListener(
        'notificationReceived',
        async (evt: NotificationReceivedEvent) => {
          if (Capacitor.getPlatform() === 'android') {
            await LocalNotifications.schedule({
              notifications: [
                {
                  id: Math.floor(Math.random() * 0x80000000), // id needs to be a 32-bit int
                  title: evt.notification.title ?? '',
                  body: evt.notification.body ?? '',
                  channelId: ANDROID_CHANNEL.id,
                  extra: evt.notification.data,
                  group: 'asa_go_alerts', // groups notifications together to mimic system notification grouping behaviour
                  groupSummary: false // don't display a summary when > 3 notifications arrive, just group them
                }
              ]
            })
          }
        }
      )

      const actionHandle = await FirebaseMessaging.addListener(
        'notificationActionPerformed',
        (evt: NotificationActionPerformedEvent) => {
          const data = evt?.notification?.data as PushNotificationData | undefined
          if (data) {
            dispatch(setPendingNotificationData(data))
          }
        }
      )

      const localActionHandle = await LocalNotifications.addListener(
        'localNotificationActionPerformed',
        (evt: ActionPerformed) => {
          const data = evt?.notification?.extra as PushNotificationData | undefined
          if (data) {
            dispatch(setPendingNotificationData(data))
          }
        }
      )

      handles.current.push(tokenHandle, receivedHandle, actionHandle, localActionHandle)
      initialized.current = true
    } catch (e) {
      console.error('Push notification error:', e)
    }
  }, [dispatch])

  useEffect(() => {
    if (!isActive || !networkStatus.connected) return

    if (currentFcmToken) {
      dispatch(registerDevice(currentFcmToken, registeredFcmToken))
    } else {
      // retry token lookup after reconnect or resume when initialization did not produce a token
      dispatch(retryPushNotificationRegistration())
    }
  }, [currentFcmToken, registeredFcmToken, networkStatus.connected, isActive, dispatch])

  useEffect(() => {
    return () => {
      if (initialized.current) {
        void FirebaseMessaging.removeAllListeners()
      }
      handles.current.forEach(h => void h.remove())
      handles.current = []
      initialized.current = false
    }
  }, [])

  return { initPushNotifications }
}
