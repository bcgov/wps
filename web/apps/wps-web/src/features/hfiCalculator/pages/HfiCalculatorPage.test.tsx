import { render, waitFor } from '@testing-library/react'
import type { FireCentre } from '@wps/api/hfiCalculatorAPI'
import { setSelectedFireCentre } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { getHFIStationsSuccess } from 'features/hfiCalculator/slices/stationsSlice'
import { Provider } from 'react-redux'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createTestStore } from '@/test/testUtils'
import HfiCalculatorPage from './HfiCalculatorPage'

const mockFetchHFIStations = vi.fn(() => ({ type: 'hfiStations/mock' }))
const mockFetchFuelTypes = vi.fn(() => ({ type: 'hfiCalc/fetchFuelTypes/mock' }))
const mockFetchGetPrepDateRange = vi.fn()
const mockFetchAllReadyStates = vi.fn()
const mockFetchToggleReadyState = vi.fn()

vi.mock('features/hfiCalculator/slices/stationsSlice', async importOriginal => {
  const actual = await importOriginal<typeof import('features/hfiCalculator/slices/stationsSlice')>()
  return { ...actual, fetchHFIStations: () => mockFetchHFIStations() }
})

vi.mock('features/hfiCalculator/slices/hfiCalculatorSlice', async importOriginal => {
  const actual = await importOriginal<typeof import('features/hfiCalculator/slices/hfiCalculatorSlice')>()
  return {
    ...actual,
    fetchFuelTypes: () => mockFetchFuelTypes(),
    fetchGetPrepDateRange: (fire_center_id: number, start_date?: string, end_date?: string) => {
      mockFetchGetPrepDateRange(fire_center_id, start_date, end_date)
      return { type: 'mock' }
    }
  }
})

vi.mock('features/hfiCalculator/slices/hfiReadySlice', async importOriginal => {
  const actual = await importOriginal<typeof import('features/hfiCalculator/slices/hfiReadySlice')>()
  return {
    ...actual,
    fetchAllReadyStates: (fire_centre_id: number, date_range: import('@wps/api/hfiCalculatorAPI').PrepDateRange) => {
      mockFetchAllReadyStates(fire_centre_id, date_range)
      return { type: 'mock' }
    },
    fetchToggleReadyState: (
      fire_centre_id: number,
      planning_area_id: number,
      date_range: import('@wps/api/hfiCalculatorAPI').PrepDateRange
    ) => {
      mockFetchToggleReadyState(fire_centre_id, planning_area_id, date_range)
      return { type: 'mock' }
    }
  }
})

// Stub out heavy child components
vi.mock('features/hfiCalculator/components/HFIPageSubHeader', () => ({
  HFIPageSubHeader: () => <div data-testid="hfi-page-sub-header" />
}))
vi.mock('features/hfiCalculator/components/HFILoadingDataContainer', () => ({
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>
}))
vi.mock('features/hfiCalculator/components/ViewSwitcherToggles', () => ({
  default: () => null
}))
vi.mock('features/hfiCalculator/components/LastUpdatedHeader', () => ({
  default: () => null
}))
vi.mock('features/hfiCalculator/components/DownloadPDFButton', () => ({
  default: () => null
}))
vi.mock('features/hfiCalculator/components/ViewSwitcher', () => ({
  default: () => null
}))
vi.mock('features/hfiCalculator/components/HFISuccessAlert', () => ({
  default: () => null
}))
vi.mock('@wps/ui/GeneralHeader', () => ({
  GeneralHeader: () => null
}))

const mockFireCentre: FireCentre = {
  id: 1,
  name: 'Kamloops Fire Centre',
  planning_areas: []
}

const mockFireCentres: FireCentre[] = [mockFireCentre]

const renderPage = (store: ReturnType<typeof createTestStore>) =>
  render(
    <Provider store={store}>
      <HfiCalculatorPage />
    </Provider>
  )

describe('HfiCalculatorPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('fetches stations and fuel types on mount', async () => {
    const store = createTestStore()
    renderPage(store)

    await waitFor(() => {
      expect(mockFetchHFIStations).toHaveBeenCalledTimes(1)
      expect(mockFetchFuelTypes).toHaveBeenCalledTimes(1)
    })
  })

  it('fetches prep date range when selected fire centre changes', async () => {
    const store = createTestStore()
    renderPage(store)

    store.dispatch(setSelectedFireCentre(mockFireCentre))

    await waitFor(() => {
      expect(mockFetchGetPrepDateRange).toHaveBeenCalledWith(mockFireCentre.id, undefined, undefined)
    })
  })

  it('stores selected fire centre name in localStorage when fire centre changes', async () => {
    const store = createTestStore()
    renderPage(store)

    store.dispatch(setSelectedFireCentre(mockFireCentre))

    await waitFor(() => {
      expect(localStorage.getItem('hfiCalcPreferredFireCentre')).toBe(mockFireCentre.name)
    })
  })

  it('restores fire centre from localStorage when fire centres load', async () => {
    localStorage.setItem('hfiCalcPreferredFireCentre', mockFireCentre.name)
    const store = createTestStore()
    renderPage(store)

    store.dispatch(getHFIStationsSuccess({ fire_centres: mockFireCentres }))

    await waitFor(() => {
      expect(store.getState().hfiCalculatorDailies.selectedFireCentre?.name).toBe(mockFireCentre.name)
    })
  })

  it('does not call fetchAllReadyStates when fire centre changes before dateRange is set', async () => {
    const store = createTestStore()
    renderPage(store)

    store.dispatch(setSelectedFireCentre(mockFireCentre))

    // dateRange is still undefined — fetchAllReadyStates must NOT fire yet
    await waitFor(() => {
      expect(mockFetchGetPrepDateRange).toHaveBeenCalled()
    })
    expect(mockFetchAllReadyStates).not.toHaveBeenCalled()
  })
})
