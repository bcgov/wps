import { combineReducers } from '@reduxjs/toolkit'
import { AppDispatch } from '@/app/store'
import { createTestStore } from '@/test/testUtils'
import { getSFMSInsightsBounds, SFMSBoundsResponse, type SFMSBounds } from '@wps/api/sfmsAPI'
import { logError } from '@wps/utils/error'
import reducer, {
  fetchSFMSInsightsBounds,
  getSFMSInsightsBoundsFailed,
  getSFMSInsightsBoundsStart,
  getSFMSInsightsBoundsSuccess,
  initialState,
  selectEarliestSFMSInsightsBounds,
  selectLatestSFMSInsightsBounds
} from './sfmsInsightsSlice'

const sfmsInsightsReducer = combineReducers({ sfmsInsights: reducer })

vi.mock('@wps/api/sfmsAPI', async () => {
  const actual = await vi.importActual<typeof import('@wps/api/sfmsAPI')>('@wps/api/sfmsAPI')
  return {
    ...actual,
    getSFMSInsightsBounds: vi.fn()
  }
})

vi.mock('@wps/utils/error', () => ({
  logError: vi.fn()
}))

const mockedGetSFMSInsightsBounds = vi.mocked(getSFMSInsightsBounds)
const mockedLogError = vi.mocked(logError)

describe('sfmsInsightsSlice reducer', () => {
  it('should return initial state for unknown action', () => {
    const next = reducer(undefined, { type: 'UNKNOWN' })
    expect(next).toEqual(initialState)
  })

  it('getSFMSInsightsBoundsStart clears bounds and sets loading', () => {
    const prev = { ...initialState, sfmsBounds: {} as SFMSBounds, sfmsBoundsError: 'old error' }
    const next = reducer(prev, getSFMSInsightsBoundsStart())

    expect(next.sfmsBounds).toBeNull()
    expect(next.sfmsBoundsLoading).toBe(true)
    expect(next.sfmsBoundsError).toBeNull()
  })

  it('getSFMSInsightsBoundsFailed sets error, clears bounds and stops loading', () => {
    const prev = { ...initialState, sfmsBounds: {} as SFMSBounds, sfmsBoundsLoading: true }
    const next = reducer(prev, getSFMSInsightsBoundsFailed('bad bounds'))

    expect(next.sfmsBounds).toBeNull()
    expect(next.sfmsBoundsLoading).toBe(false)
    expect(next.sfmsBoundsError).toBe('bad bounds')
  })

  it('getSFMSInsightsBoundsSuccess sets bounds, clears error and stops loading', () => {
    const bounds: SFMSBounds = {
      '2025': {
        actual: {
          minimum: '2025-05-01',
          maximum: '2025-10-31'
        }
      }
    }
    const prev = { ...initialState, sfmsBoundsError: 'old error', sfmsBoundsLoading: true }
    const next = reducer(prev, getSFMSInsightsBoundsSuccess({ sfms_bounds: bounds }))

    expect(next.sfmsBounds).toBe(bounds)
    expect(next.sfmsBoundsLoading).toBe(false)
    expect(next.sfmsBoundsError).toBeNull()
  })
})

describe('fetchSFMSInsightsBounds thunk', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should update state with sfmsBounds and stop loading', async () => {
    const sfmsBounds: SFMSBoundsResponse = {
      sfms_bounds: {
        '2025': {
          actual: {
            minimum: '2025-05-01',
            maximum: '2025-10-31'
          }
        }
      }
    }
    mockedGetSFMSInsightsBounds.mockResolvedValue(sfmsBounds)

    const store = createTestStore({ sfmsInsights: initialState }, sfmsInsightsReducer)
    const dispatch = store.dispatch as AppDispatch
    await dispatch(fetchSFMSInsightsBounds())

    const state = store.getState().sfmsInsights
    expect(state.sfmsBounds).toBe(sfmsBounds.sfms_bounds)
    expect(state.sfmsBoundsLoading).toBe(false)
    expect(state.sfmsBoundsError).toBeNull()
    expect(mockedLogError).not.toHaveBeenCalled()
  })

  it('should log an error and stop loading', async () => {
    const error = 'Error'
    mockedGetSFMSInsightsBounds.mockRejectedValue(error)

    const store = createTestStore({ sfmsInsights: initialState }, sfmsInsightsReducer)
    const dispatch = store.dispatch as AppDispatch
    await dispatch(fetchSFMSInsightsBounds())

    const state = store.getState().sfmsInsights
    expect(state.sfmsBounds).toBeNull()
    expect(state.sfmsBoundsLoading).toBe(false)
    expect(state.sfmsBoundsError).toBe(error)
    expect(mockedLogError).toHaveBeenCalledWith(error)
  })
})

describe('SFMS Insights bounds selectors', () => {
  it('selectLatestSFMSInsightsBounds returns actual bounds from most recent year', () => {
    const state = {
      sfmsInsights: {
        ...initialState,
        sfmsBounds: {
          '2024': {
            actual: {
              minimum: '2024-01-01',
              maximum: '2024-12-31'
            }
          },
          '2025': {
            actual: {
              minimum: '2025-01-01',
              maximum: '2025-11-02'
            }
          }
        }
      }
    }

    expect(selectLatestSFMSInsightsBounds(state)).toEqual({
      minimum: '2025-01-01',
      maximum: '2025-11-02'
    })
  })

  it('selectEarliestSFMSInsightsBounds returns actual bounds from earliest year', () => {
    const state = {
      sfmsInsights: {
        ...initialState,
        sfmsBounds: {
          '2024': {
            actual: {
              minimum: '2024-01-01',
              maximum: '2024-12-31'
            }
          },
          '2025': {
            actual: {
              minimum: '2025-01-01',
              maximum: '2025-11-02'
            }
          }
        }
      }
    }

    expect(selectEarliestSFMSInsightsBounds(state)).toEqual({
      minimum: '2024-01-01',
      maximum: '2024-12-31'
    })
  })

  it('selectLatestSFMSInsightsBounds skips years with empty maximum', () => {
    const state = {
      sfmsInsights: {
        ...initialState,
        sfmsBounds: {
          '2024': {
            actual: {
              minimum: '2024-01-01',
              maximum: ''
            }
          },
          '2025': {
            actual: {
              minimum: '',
              maximum: ''
            }
          },
          '2023': {
            actual: {
              minimum: '2023-01-01',
              maximum: '2023-12-31'
            }
          }
        }
      }
    }

    expect(selectLatestSFMSInsightsBounds(state)).toEqual({
      minimum: '2023-01-01',
      maximum: '2023-12-31'
    })
  })

  it('selectEarliestSFMSInsightsBounds skips years with empty minimum', () => {
    const state = {
      sfmsInsights: {
        ...initialState,
        sfmsBounds: {
          '2023': {
            actual: {
              minimum: '',
              maximum: '2023-12-31'
            }
          },
          '2024': {
            actual: {
              minimum: '2024-01-01',
              maximum: ''
            }
          }
        }
      }
    }

    expect(selectEarliestSFMSInsightsBounds(state)).toEqual({
      minimum: '2024-01-01',
      maximum: ''
    })
  })

  it('selectors return null when bounds are null', () => {
    const state = {
      sfmsInsights: {
        ...initialState,
        sfmsBounds: null
      }
    }

    expect(selectLatestSFMSInsightsBounds(state)).toBeNull()
    expect(selectEarliestSFMSInsightsBounds(state)).toBeNull()
  })
})
