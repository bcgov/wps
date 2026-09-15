import { describe, expect, it } from 'vitest'
import type { RootState } from '@/store'
import { selectNotificationSettingsDisabled, selectNotificationSetupState, selectOperationalDataLoading } from '@/store'

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
    provincialSummaries = {},
    tpiStats = {},
    hfiStats = {}
  }: {
    fireCentresLoading?: boolean
    runParametersLoading?: boolean
    dataLoading?: boolean
    provincialSummaries?: object | null
    tpiStats?: object | null
    hfiStats?: object | null
  } = {}) =>
    ({
      fireCentres: { loading: fireCentresLoading },
      runParameters: { loading: runParametersLoading },
      data: {
        loading: dataLoading,
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
})
