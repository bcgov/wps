import { DateTime } from 'luxon'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import reducer, {
  fetchSFMSBounds,
  fetchSFMSRunDates,
  getRunDatesFailed,
  getRunDatesStart,
  getRunDatesSuccess,
  getSFMSBoundsFailed,
  getSFMSBoundsStart,
  getSFMSBoundsSuccess,
  initialState,
  selectLatestSFMSBounds,
  selectEarliestSFMSBounds
} from '@/features/fba/slices/runDatesSlice'

import { createTestStore } from '@/test/testUtils'
import { AppDispatch } from '@/app/store'
import { combineReducers } from '@reduxjs/toolkit'
import {
  getAllRunDates,
  getMostRecentRunDate,
  getSFMSBounds,
  RunType,
  SFMSBoundsResponse,
  type SFMSBounds
} from 'api/fbaAPI'
import { logError } from 'utils/error'

const runDatesReducer = combineReducers({ runDates: reducer })

// We mock the API and error logger while keeping TS types
vi.mock('@/api/fbaAPI', async () => {
  const actual = await vi.importActual<typeof import('@/api/fbaAPI')>('@/api/fbaAPI')
  return {
    ...actual,
    getAllRunDates: vi.fn(),
    getMostRecentRunDate: vi.fn(),
    getSFMSBounds: vi.fn()
  }
})

vi.mock('utils/error', () => ({
  logError: vi.fn()
}))

// Convenience helpers for typed mocks
const mockedGetAllRunDates = vi.mocked(getAllRunDates)
const mockedGetMostRecentRunDate = vi.mocked(getMostRecentRunDate)
const mockedGetSFMSBounds = vi.mocked(getSFMSBounds)
const mockedLogError = vi.mocked(logError)

describe('runDatesSlice reducer', () => {
  it('should return initial state for unknown action', () => {
    const next = reducer(undefined, { type: 'UNKNOWN' })
    expect(next).toEqual(initialState)
  })

  it('getRunDatesStart resets runDates and sets loading', () => {
    const prev = {
      ...initialState,
      error: 'previous error',
      runDates: [DateTime.fromISO('2025-01-01')],
      mostRecentRunDate: '2025-01-01',
      loading: false
    }

    const next = reducer(prev, getRunDatesStart())
    expect(next.loading).toBe(true)
    expect(next.error).toBeNull()
    expect(next.runDates).toEqual([])
    expect(next.mostRecentRunDate).toBeNull()
  })

  it('getRunDatesFailed sets error and stops loading', () => {
    const prev = { ...initialState, loading: true }
    const next = reducer(prev, getRunDatesFailed('boom'))
    expect(next.loading).toBe(false)
    expect(next.error).toBe('boom')
  })

  it('getRunDatesSuccess sets runDates and mostRecentRunDate, resets error and loading', () => {
    const prev = { ...initialState, loading: true, error: 'err' }
    const runDates = [DateTime.fromISO('2025-01-01'), DateTime.fromISO('2025-01-02')]
    const next = reducer(prev, getRunDatesSuccess({ runDates, mostRecentRunDate: '2025-01-02' }))

    expect(next.loading).toBe(false)
    expect(next.error).toBeNull()
    expect(next.runDates).toEqual(runDates)
    expect(next.mostRecentRunDate).toBe('2025-01-02')
  })

  it('getSFMSBoundsStart clears sfmsBounds', () => {
    const prev = { ...initialState, sfmsBounds: {} as SFMSBounds }
    const next = reducer(prev, getSFMSBoundsStart())
    expect(next.sfmsBounds).toBeNull()
  })

  it('getSFMSBoundsFailed sets sfmsBoundsError and clears sfmsBounds', () => {
    const prev = { ...initialState, sfmsBounds: {} as SFMSBounds }
    const next = reducer(prev, getSFMSBoundsFailed('bad bounds'))
    expect(next.sfmsBounds).toBeNull()
    expect(next.sfmsBoundsError).toBe('bad bounds')
  })

  it('getSFMSBoundsSuccess sets bounds and clears error', () => {
    const prev = { ...initialState, sfmsBoundsError: 'oops' }
    const bounds: SFMSBounds = {
      2025: {
        forecast: {
          minimum: '2025-05-01',
          maximum: '2025-10-31'
        }
      }
    }
    const next = reducer(prev, getSFMSBoundsSuccess({ sfms_bounds: bounds }))
    expect(next.sfmsBoundsError).toBeNull()
    expect(next.sfmsBounds).toEqual(bounds)
  })
})

describe('fetchSFMSRunDates thunk', () => {
  const runType = RunType.FORECAST
  const forDate = '2025-01-03'
  const runDates = [DateTime.fromISO('2025-01-01'), DateTime.fromISO('2025-01-02')]
  const mostRecentRunDate = '2025-01-02'
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should update state with runDates and mostRecentRunDate', async () => {
    mockedGetAllRunDates.mockResolvedValue(runDates)
    mockedGetMostRecentRunDate.mockResolvedValue(mostRecentRunDate)

    const store = createTestStore({ runDates: initialState }, runDatesReducer)
    const dispatch = store.dispatch as AppDispatch
    await dispatch(fetchSFMSRunDates(runType, forDate))

    const runDatesState = store.getState().runDates
    expect(runDatesState.loading).toBe(false)
    expect(runDatesState.runDates).toBe(runDates)
    expect(runDatesState.mostRecentRunDate).toBe(mostRecentRunDate)
    expect(runDatesState.error).toBeNull()
    expect(mockedLogError).not.toHaveBeenCalled()
  })

  it('should log an error', async () => {
    const error = 'Error'
    mockedGetAllRunDates.mockRejectedValue(error)
    const store = createTestStore({ runDates: initialState }, runDatesReducer)
    const dispatch = store.dispatch as AppDispatch
    await dispatch(fetchSFMSRunDates(runType, forDate))
    const runDatesState = store.getState().runDates
    expect(runDatesState.error).toBe(error)
    expect(mockedLogError).toHaveBeenCalled()
  })
})

describe('fetchSFMSBounds thunk', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should update state with runDates and mostRecentRunDate', async () => {
    const sfmsBounds: SFMSBoundsResponse = {
      sfms_bounds: {
        2025: {
          forecast: {
            minimum: '2025-05-01',
            maximum: '2025-10-31'
          }
        }
      }
    }
    mockedGetSFMSBounds.mockResolvedValue(sfmsBounds)
    const store = createTestStore({ runDates: initialState }, runDatesReducer)
    const dispatch = store.dispatch as AppDispatch
    await dispatch(fetchSFMSBounds())

    const runDatesState = store.getState().runDates
    expect(runDatesState.loading).toBe(false)
    expect(runDatesState.sfmsBoundsError).toBeNull()
    expect(runDatesState.sfmsBounds).toBe(sfmsBounds.sfms_bounds)
  })

  it('should log an error', async () => {
    const error = 'Error'
    mockedGetSFMSBounds.mockRejectedValue(error)
    const store = createTestStore({ runDates: initialState }, runDatesReducer)
    const dispatch = store.dispatch as AppDispatch
    await dispatch(fetchSFMSBounds())
    const runDatesState = store.getState().runDates
    expect(runDatesState.sfmsBoundsError).toBe(error)
    expect(mockedLogError).toHaveBeenCalled()
  })
})

describe('SFMS bounds selectors', () => {
  it('selectLatestSFMSBounds returns bounds from most recent year', () => {
    const state = {
      runDates: {
        ...initialState,
        sfmsBounds: {
          '2024': {
            forecast: {
              minimum: '2024-01-01',
              maximum: '2024-12-31'
            }
          },
          '2025': {
            forecast: {
              minimum: '2025-01-01',
              maximum: '2025-11-02'
            }
          }
        }
      }
    }

    const result = selectLatestSFMSBounds(state)
    expect(result).toEqual({
      minimum: '2025-01-01',
      maximum: '2025-11-02'
    })
  })

  it('selectLatestSFMSBounds returns null when sfmsBounds is null', () => {
    const state = {
      runDates: {
        ...initialState,
        sfmsBounds: null
      }
    }

    const result = selectLatestSFMSBounds(state)
    expect(result).toBeNull()
  })

  it('selectLatestSFMSBounds skips years without maximum', () => {
    const state = {
      runDates: {
        ...initialState,
        sfmsBounds: {
          '2024': {
            forecast: {
              minimum: '2024-01-01',
              maximum: ''
            }
          },
          '2023': {
            forecast: {
              minimum: '2023-01-01',
              maximum: '2023-12-31'
            }
          }
        }
      }
    }

    const result = selectLatestSFMSBounds(state)
    expect(result).toEqual({
      minimum: '2023-01-01',
      maximum: '2023-12-31'
    })
  })

  it('selectEarliestSFMSBounds returns bounds from earliest year', () => {
    const state = {
      runDates: {
        ...initialState,
        sfmsBounds: {
          '2024': {
            forecast: {
              minimum: '2024-01-01',
              maximum: '2024-12-31'
            }
          },
          '2025': {
            forecast: {
              minimum: '2025-01-01',
              maximum: '2025-11-02'
            }
          }
        }
      }
    }

    const result = selectEarliestSFMSBounds(state)
    expect(result).toEqual({
      minimum: '2024-01-01',
      maximum: '2024-12-31'
    })
  })

  it('selectEarliestSFMSBounds returns null when sfmsBounds is null', () => {
    const state = {
      runDates: {
        ...initialState,
        sfmsBounds: null
      }
    }

    const result = selectEarliestSFMSBounds(state)
    expect(result).toBeNull()
  })

  it('selectEarliestSFMSBounds skips years without minimum', () => {
    const state = {
      runDates: {
        ...initialState,
        sfmsBounds: {
          '2023': {
            forecast: {
              minimum: '',
              maximum: '2023-12-31'
            }
          },
          '2024': {
            forecast: {
              minimum: '2024-01-01',
              maximum: '2024-12-31'
            }
          }
        }
      }
    }

    const result = selectEarliestSFMSBounds(state)
    expect(result).toEqual({
      minimum: '2024-01-01',
      maximum: '2024-12-31'
    })
  })
})
