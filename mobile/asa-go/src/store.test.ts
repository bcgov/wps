import { describe, expect, it } from 'vitest'
import type { RootState } from '@/store'
import {
  selectMapLayersLoadState,
  selectNotificationSettingsDisabled,
  selectNotificationSetupState,
  selectOperationalDataLoading,
  selectOperationalLoadState,
  selectSettingsLoadState
} from '@/store'

const base: {
  pushNotificationPermission: 'granted' | 'denied'
  registeredFcmToken: string | null
  deviceIdError: boolean
  registrationError: boolean
} = {
  pushNotificationPermission: 'granted' as const,
  registeredFcmToken: 'some-token',
  deviceIdError: false,
  registrationError: false
}

const makeState = (overrides: Partial<typeof base>, connected = true): RootState =>
  ({
    settings: {
      loading: false,
      error: null,
      fireCentreInfos: [],
      pinnedFireCentre: null,
      subscriptions: [],
      subscriptionsInitialized: true
    },
    pushNotification: {
      ...base,
      ...overrides
    },
    networkStatus: {
      networkStatus: { connected, connectionType: connected ? 'wifi' : 'none' }
    }
  }) as unknown as RootState

describe('selectNotificationSetupState', () => {
  it('returns permissionDenied when permission is denied', () => {
    expect(selectNotificationSetupState(makeState({ pushNotificationPermission: 'denied' }))).toBe('permissionDenied')
  })

  it('returns permissionDenied when permission is unknown', () => {
    expect(selectNotificationSetupState(makeState({ pushNotificationPermission: 'unknown' as never }))).toBe(
      'permissionDenied'
    )
  })

  it('returns unregistered when registeredFcmToken is null', () => {
    expect(selectNotificationSetupState(makeState({ registeredFcmToken: null }))).toBe('unregistered')
  })

  it('returns registrationFailed when token is null and registrationError is true', () => {
    expect(selectNotificationSetupState(makeState({ registeredFcmToken: null, registrationError: true }))).toBe(
      'registrationFailed'
    )
  })

  it('returns ready when permission granted and registeredFcmToken is set', () => {
    expect(selectNotificationSetupState(makeState({}))).toBe('ready')
  })
})

describe('selectNotificationSettingsDisabled', () => {
  it('returns false when ready and online', () => {
    expect(selectNotificationSettingsDisabled(makeState({}))).toBe(false)
  })

  it('returns true when permission denied', () => {
    expect(selectNotificationSettingsDisabled(makeState({ pushNotificationPermission: 'denied' }))).toBe(true)
  })

  it('returns true when unregistered', () => {
    expect(selectNotificationSettingsDisabled(makeState({ registeredFcmToken: undefined }))).toBe(true)
  })

  it('returns true when offline', () => {
    expect(selectNotificationSettingsDisabled(makeState({}, false))).toBe(true)
  })

  it('returns true when subscriptions are not yet initialized', () => {
    const state = { ...makeState({}), settings: { ...makeState({}).settings, subscriptionsInitialized: false } }
    expect(selectNotificationSettingsDisabled(state as RootState)).toBe(true)
  })
})

describe('selectOperationalDataLoading', () => {
  const makeOperationalState = ({
    fireCentresLoading = false,
    runParametersLoading = false,
    dataLoading = false,
    dataError = null,
    fireCentresError = null,
    runParametersError = null,
    provincialSummaries = {},
    tpiStats = {},
    hfiStats = {}
  }: {
    fireCentresLoading?: boolean
    runParametersLoading?: boolean
    dataLoading?: boolean
    dataError?: string | null
    fireCentresError?: string | null
    runParametersError?: string | null
    provincialSummaries?: object | null
    tpiStats?: object | null
    hfiStats?: object | null
  } = {}) =>
    ({
      fireCentres: { loading: fireCentresLoading, error: fireCentresError },
      runParameters: { loading: runParametersLoading, error: runParametersError },
      data: {
        loading: dataLoading,
        error: dataError,
        provincialSummaries,
        tpiStats,
        hfiStats
      }
    }) as unknown as RootState

  it.each([
    ['fire centres', { fireCentresLoading: true }],
    ['operational data', { dataLoading: true }]
  ])('returns true while %s are loading', (_label, loading) =>
    expect(selectOperationalDataLoading(makeOperationalState(loading))).toBe(true)
  )

  it.each(['provincialSummaries', 'tpiStats', 'hfiStats'] as const)(
    'returns true while run parameters load before %s are available',
    missingDataKey => {
      const state = makeOperationalState({
        runParametersLoading: true,
        [missingDataKey]: null
      })

      expect(selectOperationalDataLoading(state)).toBe(true)
    }
  )

  it('returns false during a run-parameter freshness check when operational data is available', () => {
    const state = makeOperationalState({ runParametersLoading: true })

    expect(selectOperationalDataLoading(state)).toBe(false)
  })

  it('returns false when operational data is idle', () => {
    const state = makeOperationalState({
      provincialSummaries: null,
      tpiStats: null,
      hfiStats: null
    })

    expect(selectOperationalDataLoading(state)).toBe(false)
  })

  it('combines operational errors into one stable error key', () => {
    const state = makeOperationalState({ dataError: 'data', fireCentresError: 'centres' })

    expect(selectOperationalLoadState(state).errorKey).toBe('data|centres')
  })
})

describe('normalized load-state selectors', () => {
  it('exposes settings loading and errors through the shared shape', () => {
    const state = {
      settings: { loading: true, error: 'settings failed' }
    } as unknown as RootState

    expect(selectSettingsLoadState(state)).toEqual({ loading: true, errorKey: 'settings failed' })
  })

  it('exposes pending map loads and the latest layer failure', () => {
    const state = {
      mapLayers: { pendingLoads: 2, latestErrorVersion: 3 }
    } as unknown as RootState

    expect(selectMapLayersLoadState(state)).toEqual({ loading: true, errorKey: '3' })
  })
})
