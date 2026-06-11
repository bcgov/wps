import { renderHook } from '@testing-library/react'
import { Provider } from 'react-redux'
import { describe, expect, it } from 'vitest'
import type { RootState } from '@/app/rootReducer'
import { createTestStore } from '@/test/testUtils'
import { useLoading } from './useLoading'

const getStore = (asaLoading: boolean) =>
  createTestStore({
    provincialSummary: { loading: asaLoading },
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
