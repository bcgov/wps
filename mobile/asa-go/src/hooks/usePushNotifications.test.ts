import { Capacitor } from '@capacitor/core'
import { LocalNotifications } from '@capacitor/local-notifications'
import { FirebaseMessaging, type PermissionStatus } from '@capacitor-firebase/messaging'
import { act, renderHook } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useAppIsActive } from '@/hooks/useAppIsActive'
import { usePushNotifications } from './usePushNotifications'

vi.mock('@capacitor-firebase/messaging', () => ({
  FirebaseMessaging: {
    checkPermissions: vi.fn(),
    requestPermissions: vi.fn(),
    createChannel: vi.fn(),
    getToken: vi.fn(),
    addListener: vi.fn(),
    removeAllListeners: vi.fn().mockResolvedValue(undefined)
  },
  Importance: { High: 4 }
}))

vi.mock(import('@capacitor/core'), async importOriginal => {
  const actual = await importOriginal()
  return {
    ...actual,
    Capacitor: {
      ...actual.Capacitor,
      getPlatform: vi.fn().mockReturnValue('android')
    }
  }
})

vi.mock('@capacitor/local-notifications', () => ({
  LocalNotifications: {
    schedule: vi.fn().mockResolvedValue(undefined),
    addListener: vi.fn().mockResolvedValue({ remove: vi.fn().mockResolvedValue(undefined) })
  }
}))

vi.mock('@/hooks/useAppIsActive', () => ({
  useAppIsActive: vi.fn().mockReturnValue(true)
}))

const mockDispatch = vi.fn()
vi.mock('react-redux', () => ({
  useDispatch: () => mockDispatch,
  useSelector: vi.fn((selector: (s: unknown) => unknown) =>
    selector({
      pushNotification: {
        registrationError: false,
        registeredFcmToken: null,
        pushNotificationPermission: 'unknown',
        deviceIdError: false
      },
      networkStatus: {
        networkStatus: { connected: false, connectionType: 'none' }
      }
    })
  )
}))

vi.mock('@/slices/pushNotificationSlice', async importOriginal => {
  const actual = await importOriginal<typeof import('@/slices/pushNotificationSlice')>()
  return {
    ...actual,
    registerDevice: vi.fn((token: string, registered: string | null) => ({
      type: 'registerDevice',
      token,
      registered
    })),
    retryPushNotificationRegistration: vi.fn(() => ({
      type: 'retryPushNotificationRegistration'
    })),
    setRegistrationError: vi.fn((value: boolean) => ({
      type: 'setRegistrationError',
      value
    }))
  }
})

function setupFirebaseMocks({ token = 'test-fcm-token', permissionStatus = 'granted' } = {}) {
  vi.mocked(FirebaseMessaging.checkPermissions).mockResolvedValue({
    receive: permissionStatus
  } as PermissionStatus)
  vi.mocked(FirebaseMessaging.getToken).mockResolvedValue({ token })
  vi.mocked(FirebaseMessaging.addListener).mockResolvedValue({
    remove: vi.fn().mockResolvedValue(undefined)
  })
}

const defaultSelectorState = {
  pushNotification: {
    registrationError: false,
    registeredFcmToken: null,
    pushNotificationPermission: 'unknown',
    deviceIdError: false
  },
  networkStatus: {
    networkStatus: { connected: false, connectionType: 'none' }
  }
}

function setupListenerCapture() {
  const fbListeners: Record<string, (...args: unknown[]) => unknown> = {}
  const localListeners: Record<string, (...args: unknown[]) => unknown> = {}

  vi.mocked(FirebaseMessaging.addListener).mockImplementation(async (event, handler) => {
    fbListeners[event as string] = handler as (...args: unknown[]) => unknown
    return { remove: vi.fn().mockResolvedValue(undefined) }
  })
  vi.mocked(LocalNotifications.addListener).mockImplementation(async (event, handler) => {
    localListeners[event as string] = handler as (...args: unknown[]) => unknown
    return { remove: vi.fn().mockResolvedValue(undefined) }
  })

  return { fbListeners, localListeners }
}

describe('usePushNotifications', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    vi.mocked(Capacitor.getPlatform).mockReturnValue('android')
    const { useSelector } = await import('react-redux')
    vi.mocked(useSelector).mockImplementation((selector: (s: unknown) => unknown) => selector(defaultSelectorState))
  })

  it('exposes push notification initialization', () => {
    const { result } = renderHook(() => usePushNotifications())
    expect(result.current.initPushNotifications).toBeInstanceOf(Function)
  })

  it('sets token after successful init', async () => {
    const { setPushNotificationPermission } = await import('@/slices/pushNotificationSlice')
    setupFirebaseMocks({ token: 'test-fcm-token' })
    const { result } = renderHook(() => usePushNotifications())

    await act(async () => {
      await result.current.initPushNotifications()
    })

    expect(FirebaseMessaging.getToken).toHaveBeenCalledTimes(1)
    expect(mockDispatch).toHaveBeenCalledWith(setPushNotificationPermission('granted'))
  })

  it('updates token when tokenReceived fires', async () => {
    let tokenListener: ((e: { token: string }) => void) | undefined
    setupFirebaseMocks({ token: 'initial-token' })
    vi.mocked(FirebaseMessaging.addListener).mockImplementation(async (event, handler) => {
      if (String(event) === 'tokenReceived') tokenListener = handler as unknown as typeof tokenListener
      return { remove: vi.fn().mockResolvedValue(undefined) }
    })
    const { registerDevice } = await import('@/slices/pushNotificationSlice')
    const { useSelector } = await import('react-redux')
    vi.mocked(useSelector).mockImplementation((selector: (s: unknown) => unknown) =>
      selector({
        pushNotification: {
          registrationError: false,
          registeredFcmToken: null,
          pushNotificationPermission: 'unknown',
          deviceIdError: false
        },
        networkStatus: {
          networkStatus: { connected: true, connectionType: 'wifi' }
        }
      })
    )

    const { result } = renderHook(() => usePushNotifications())
    await act(async () => {
      await result.current.initPushNotifications()
    })

    await act(async () => {
      tokenListener?.({ token: 'refreshed-token' })
    })

    expect(mockDispatch).toHaveBeenCalledWith(registerDevice('refreshed-token', null))
  })

  it('prevents multiple initializations', async () => {
    setupFirebaseMocks()
    const { result } = renderHook(() => usePushNotifications())

    await act(async () => {
      await result.current.initPushNotifications()
      await result.current.initPushNotifications()
    })

    expect(FirebaseMessaging.getToken).toHaveBeenCalledTimes(1)
  })

  it('requests permissions when not initially granted', async () => {
    const { setPushNotificationPermission } = await import('@/slices/pushNotificationSlice')
    vi.mocked(FirebaseMessaging.checkPermissions).mockResolvedValue({
      receive: 'denied'
    } as PermissionStatus)
    vi.mocked(FirebaseMessaging.requestPermissions).mockResolvedValue({
      receive: 'granted'
    } as PermissionStatus)
    vi.mocked(FirebaseMessaging.getToken).mockResolvedValue({
      token: 'test-token'
    })
    vi.mocked(FirebaseMessaging.addListener).mockResolvedValue({
      remove: vi.fn().mockResolvedValue(undefined)
    })

    const { result } = renderHook(() => usePushNotifications())
    await act(async () => {
      await result.current.initPushNotifications()
    })

    expect(FirebaseMessaging.requestPermissions).toHaveBeenCalledTimes(1)
    expect(mockDispatch).toHaveBeenCalledWith(setPushNotificationPermission('denied'))
    expect(mockDispatch).toHaveBeenCalledWith(setPushNotificationPermission('granted'))
  })

  it('does not throw when permissions are denied', async () => {
    const { setPushNotificationPermission } = await import('@/slices/pushNotificationSlice')
    vi.mocked(FirebaseMessaging.checkPermissions).mockResolvedValue({
      receive: 'denied'
    } as PermissionStatus)
    vi.mocked(FirebaseMessaging.requestPermissions).mockResolvedValue({
      receive: 'denied'
    } as PermissionStatus)
    vi.mocked(FirebaseMessaging.addListener).mockResolvedValue({
      remove: vi.fn().mockResolvedValue(undefined)
    })

    const { result } = renderHook(() => usePushNotifications())
    await expect(
      act(async () => {
        await result.current.initPushNotifications()
      })
    ).resolves.not.toThrow()
    expect(mockDispatch).toHaveBeenCalledWith(setPushNotificationPermission('denied'))
  })

  it('dispatches setRegistrationError when getToken fails during init', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const { setPushNotificationPermission, setRegistrationError } = await import('@/slices/pushNotificationSlice')
    vi.mocked(FirebaseMessaging.checkPermissions).mockResolvedValue({
      receive: 'granted'
    } as PermissionStatus)
    vi.mocked(FirebaseMessaging.getToken).mockRejectedValue(new Error('token error'))

    const { result } = renderHook(() => usePushNotifications())
    await act(async () => {
      await result.current.initPushNotifications()
    })

    expect(mockDispatch).toHaveBeenCalledWith(setPushNotificationPermission('granted'))
    expect(mockDispatch).toHaveBeenCalledWith(setRegistrationError(true))
    consoleSpy.mockRestore()
  })

  it('does not dispatch setRegistrationError when permissions are denied', async () => {
    const { setRegistrationError } = await import('@/slices/pushNotificationSlice')
    vi.mocked(FirebaseMessaging.checkPermissions).mockResolvedValue({
      receive: 'denied'
    } as PermissionStatus)
    vi.mocked(FirebaseMessaging.requestPermissions).mockResolvedValue({
      receive: 'denied'
    } as PermissionStatus)

    const { result } = renderHook(() => usePushNotifications())
    await act(async () => {
      await result.current.initPushNotifications()
    })

    expect(mockDispatch).not.toHaveBeenCalledWith(setRegistrationError(true))
  })

  it('does not create Android channel on iOS', async () => {
    vi.mocked(Capacitor.getPlatform).mockReturnValue('ios')
    setupFirebaseMocks()

    const { result } = renderHook(() => usePushNotifications())
    await act(async () => {
      await result.current.initPushNotifications()
    })

    expect(FirebaseMessaging.createChannel).not.toHaveBeenCalled()
  })

  it('removes all listeners on unmount only when initialized', async () => {
    const remove1 = vi.fn().mockResolvedValue(undefined)
    const remove2 = vi.fn().mockResolvedValue(undefined)
    const remove3 = vi.fn().mockResolvedValue(undefined)
    vi.mocked(FirebaseMessaging.addListener)
      .mockResolvedValueOnce({ remove: remove1 })
      .mockResolvedValueOnce({ remove: remove2 })
      .mockResolvedValueOnce({ remove: remove3 })
    setupFirebaseMocks()

    const { result, unmount } = renderHook(() => usePushNotifications())
    await act(async () => {
      await result.current.initPushNotifications()
    })

    unmount()

    expect(FirebaseMessaging.removeAllListeners).toHaveBeenCalledTimes(1)
    expect(remove1).toHaveBeenCalledTimes(1)
    expect(remove2).toHaveBeenCalledTimes(1)
    expect(remove3).toHaveBeenCalledTimes(1)
  })

  it('does not call removeAllListeners on unmount when not initialized', () => {
    const { unmount } = renderHook(() => usePushNotifications())
    unmount()
    expect(FirebaseMessaging.removeAllListeners).not.toHaveBeenCalled()
  })

  describe('registerDevice effect', () => {
    it('dispatches registerDevice when connected and token is available', async () => {
      const { registerDevice } = await import('@/slices/pushNotificationSlice')
      const { useSelector } = await import('react-redux')
      vi.mocked(useSelector).mockImplementation((selector: (s: unknown) => unknown) =>
        selector({
          pushNotification: {
            registrationError: false,
            registeredFcmToken: null,
            pushNotificationPermission: 'unknown',
            deviceIdError: false
          },
          networkStatus: {
            networkStatus: { connected: true, connectionType: 'wifi' }
          }
        })
      )
      setupFirebaseMocks({ token: 'test-fcm-token' })

      const { result } = renderHook(() => usePushNotifications())
      await act(async () => {
        await result.current.initPushNotifications()
      })

      expect(mockDispatch).toHaveBeenCalledWith(registerDevice('test-fcm-token', null))
    })

    it('does not dispatch registerDevice when offline', async () => {
      const { registerDevice } = await import('@/slices/pushNotificationSlice')
      setupFirebaseMocks({ token: 'test-fcm-token' })

      const { result } = renderHook(() => usePushNotifications())
      await act(async () => {
        await result.current.initPushNotifications()
      })

      expect(mockDispatch).not.toHaveBeenCalledWith(registerDevice('test-fcm-token', null))
    })

    it('retries token lookup after reconnecting', async () => {
      const { retryPushNotificationRegistration } = await import('@/slices/pushNotificationSlice')
      const { useSelector } = await import('react-redux')
      let connected = false
      vi.mocked(useSelector).mockImplementation((selector: (s: unknown) => unknown) =>
        selector({
          ...defaultSelectorState,
          pushNotification: {
            ...defaultSelectorState.pushNotification,
            registrationError: true
          },
          networkStatus: {
            networkStatus: { connected, connectionType: connected ? 'wifi' : 'none' }
          }
        })
      )

      const { rerender } = renderHook(() => usePushNotifications())
      expect(mockDispatch).not.toHaveBeenCalledWith(retryPushNotificationRegistration())

      connected = true
      rerender()

      expect(mockDispatch).toHaveBeenCalledWith(retryPushNotificationRegistration())
    })

    it('retries token lookup after the app resumes', async () => {
      const { retryPushNotificationRegistration } = await import('@/slices/pushNotificationSlice')
      const { useSelector } = await import('react-redux')
      vi.mocked(useSelector).mockImplementation((selector: (s: unknown) => unknown) =>
        selector({
          ...defaultSelectorState,
          pushNotification: {
            ...defaultSelectorState.pushNotification,
            registrationError: true
          },
          networkStatus: {
            networkStatus: { connected: true, connectionType: 'wifi' }
          }
        })
      )
      vi.mocked(useAppIsActive).mockReturnValue(false)

      const { rerender } = renderHook(() => usePushNotifications())
      expect(mockDispatch).not.toHaveBeenCalledWith(retryPushNotificationRegistration())

      vi.mocked(useAppIsActive).mockReturnValue(true)
      rerender()

      expect(mockDispatch).toHaveBeenCalledWith(retryPushNotificationRegistration())
    })
  })

  describe('notification listeners', () => {
    it('schedules a local notification when notificationReceived fires on Android', async () => {
      vi.mocked(Capacitor.getPlatform).mockReturnValue('android')
      setupFirebaseMocks()
      const { fbListeners } = setupListenerCapture()

      const { result } = renderHook(() => usePushNotifications())
      await act(async () => {
        await result.current.initPushNotifications()
      })

      await act(async () => {
        await fbListeners.notificationReceived?.({
          notification: {
            title: 'Test Alert',
            body: 'Zone 1 is at high risk',
            data: { advisory_date: '2025-07-02', fire_centre_id: '1', fire_zone_unit: '42' }
          }
        })
      })

      expect(LocalNotifications.schedule).toHaveBeenCalledWith({
        notifications: [
          expect.objectContaining({
            title: 'Test Alert',
            body: 'Zone 1 is at high risk',
            channelId: 'general',
            group: 'asa_go_alerts',
            groupSummary: false
          })
        ]
      })
    })

    it('does not schedule a local notification when notificationReceived fires on iOS', async () => {
      vi.mocked(Capacitor.getPlatform).mockReturnValue('ios')
      setupFirebaseMocks()
      const { fbListeners } = setupListenerCapture()

      const { result } = renderHook(() => usePushNotifications())
      await act(async () => {
        await result.current.initPushNotifications()
      })

      await act(async () => {
        await fbListeners.notificationReceived?.({
          notification: { title: 'Test', body: 'Body', data: {} }
        })
      })

      expect(LocalNotifications.schedule).not.toHaveBeenCalled()
    })

    it('dispatches setPendingNotificationData when notificationActionPerformed fires with data', async () => {
      setupFirebaseMocks()
      const { fbListeners } = setupListenerCapture()
      const { setPendingNotificationData } = await import('@/slices/pushNotificationSlice')
      const notificationData = {
        advisory_date: '2025-07-02',
        fire_centre_id: '1',
        fire_zone_unit: '42'
      }

      const { result } = renderHook(() => usePushNotifications())
      await act(async () => {
        await result.current.initPushNotifications()
      })

      act(() => {
        fbListeners.notificationActionPerformed?.({
          notification: { data: notificationData }
        })
      })

      expect(mockDispatch).toHaveBeenCalledWith(setPendingNotificationData(notificationData))
    })

    it('does not dispatch when notificationActionPerformed fires without data', async () => {
      setupFirebaseMocks()
      const { fbListeners } = setupListenerCapture()
      const { setPendingNotificationData } = await import('@/slices/pushNotificationSlice')

      const { result } = renderHook(() => usePushNotifications())
      await act(async () => {
        await result.current.initPushNotifications()
      })

      act(() => {
        fbListeners.notificationActionPerformed?.({
          notification: { data: undefined }
        })
      })

      expect(mockDispatch).not.toHaveBeenCalledWith(setPendingNotificationData(expect.anything()))
    })

    it('dispatches setPendingNotificationData when localNotificationActionPerformed fires with extra', async () => {
      setupFirebaseMocks()
      const { localListeners } = setupListenerCapture()
      const { setPendingNotificationData } = await import('@/slices/pushNotificationSlice')
      const notificationData = {
        advisory_date: '2025-07-02',
        fire_centre_id: '2',
        fire_zone_unit: '99'
      }

      const { result } = renderHook(() => usePushNotifications())
      await act(async () => {
        await result.current.initPushNotifications()
      })

      act(() => {
        localListeners.localNotificationActionPerformed?.({
          notification: { extra: notificationData }
        })
      })

      expect(mockDispatch).toHaveBeenCalledWith(setPendingNotificationData(notificationData))
    })

    it('does not dispatch when localNotificationActionPerformed fires without extra', async () => {
      setupFirebaseMocks()
      const { localListeners } = setupListenerCapture()
      const { setPendingNotificationData } = await import('@/slices/pushNotificationSlice')

      const { result } = renderHook(() => usePushNotifications())
      await act(async () => {
        await result.current.initPushNotifications()
      })

      act(() => {
        localListeners.localNotificationActionPerformed?.({
          notification: { extra: undefined }
        })
      })

      expect(mockDispatch).not.toHaveBeenCalledWith(setPendingNotificationData(expect.anything()))
    })
  })
})
