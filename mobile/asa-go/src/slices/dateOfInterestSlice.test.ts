import { DateTime } from 'luxon'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import reducer, {
  resetDateOfInterestIfStale,
  selectDateOfInterest,
  selectDateOfInterestKey,
  setDateOfInterest
} from '@/slices/dateOfInterestSlice'
import type { RootState } from '@/store'
import { createTestStore } from '@/testUtils'
import { ASA_GO_TIMEZONE } from '@/utils/constants'

const mockGetTodayKey = vi.hoisted(() => vi.fn())

vi.mock('@/utils/dataSliceUtils', () => ({
  getTodayKey: mockGetTodayKey
}))

describe('dateOfInterestSlice', () => {
  beforeEach(() => {
    mockGetTodayKey.mockReturnValue('2025-07-02')
  })

  it('initializes from the current ASA Go day at store creation', () => {
    expect(reducer(undefined, { type: 'unknown' })).toEqual({ dateKey: '2025-07-02' })

    mockGetTodayKey.mockReturnValue('2025-07-03')

    expect(reducer(undefined, { type: 'unknown' })).toEqual({ dateKey: '2025-07-03' })
  })

  it('sets the selected date key', () => {
    expect(reducer({ dateKey: '2025-07-02' }, setDateOfInterest('2025-07-03'))).toEqual({
      dateKey: '2025-07-03'
    })
  })

  it('selects the raw key and a memoized DateTime in the ASA Go timezone', () => {
    const state = { dateOfInterest: { dateKey: '2025-07-03' } } as RootState

    expect(selectDateOfInterestKey(state)).toBe('2025-07-03')
    expect(selectDateOfInterest(state).equals(DateTime.fromISO('2025-07-03', { zone: ASA_GO_TIMEZONE }))).toBe(true)
    expect(selectDateOfInterest(state)).toBe(selectDateOfInterest(state))
  })

  it('advances a stale selected date to today', () => {
    const store = createTestStore({ dateOfInterest: { dateKey: '2025-07-01' } })

    store.dispatch(resetDateOfInterestIfStale())

    expect(store.getState().dateOfInterest.dateKey).toBe('2025-07-02')
  })

  it('preserves today and future dates', () => {
    const todayStore = createTestStore({ dateOfInterest: { dateKey: '2025-07-02' } })
    const tomorrowStore = createTestStore({ dateOfInterest: { dateKey: '2025-07-03' } })

    todayStore.dispatch(resetDateOfInterestIfStale())
    tomorrowStore.dispatch(resetDateOfInterestIfStale())

    expect(todayStore.getState().dateOfInterest.dateKey).toBe('2025-07-02')
    expect(tomorrowStore.getState().dateOfInterest.dateKey).toBe('2025-07-03')
  })
})
