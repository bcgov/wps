import { renderHook, act } from '@testing-library/react'
import { Provider } from 'react-redux'
import { describe, it, expect, vi } from 'vitest'
import { useLoading } from './useLoading'
import { createTestStore } from '@/test/testUtils'
import { RootState } from '@/app/rootReducer'

const getStore = (asaLoading: boolean) =>
  createTestStore({
    fireZoneStatus: { loading: asaLoading },
    provincialSummary: { loading: false },
    fireCentreHFIFuelStats: { loading: false },
    fireCentreTPIStats: { loading: false },
    runDates: { loading: false }
  } as Partial<RootState>)

describe('useLoading', () => {
  it('returns false initially when not loading', () => {
    const store = getStore(false)
    const { result } = renderHook(() => useLoading(), {
      wrapper: ({ children }) => <Provider store={store}>{children}</Provider>
    })
    expect(result.current).toBe(false)
  })

  it('returns true immediately when loading is true', () => {
    const store = getStore(true)
    const { result } = renderHook(() => useLoading(), {
      wrapper: ({ children }) => <Provider store={store}>{children}</Provider>
    })
    expect(result.current).toBe(true)
  })
})
