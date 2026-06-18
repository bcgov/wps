import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { fetchPercentiles } from 'features/percentileCalculator/slices/percentilesSlice'
import { Provider } from 'react-redux'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createTestStore } from '@/test/testUtils'
import PercentileCalculatorPage from './PercentileCalculatorPage'

const MOCKED_CURRENT_YEAR = 2024

vi.mock('@wps/api/stationAPI', () => ({
  getStations: vi.fn(() => Promise.resolve([])),
  StationSource: { unspecified: 'unspecified' }
}))

vi.mock('features/stations/slices/stationsSlice', async () => {
  const actual = await vi.importActual<typeof import('features/stations/slices/stationsSlice')>(
    'features/stations/slices/stationsSlice'
  )
  return { ...actual, fetchWxStations: vi.fn(() => () => {}) }
})

vi.mock('features/percentileCalculator/slices/percentilesSlice', async () => {
  const actual = await vi.importActual<typeof import('features/percentileCalculator/slices/percentilesSlice')>(
    'features/percentileCalculator/slices/percentilesSlice'
  )
  return { ...actual, fetchPercentiles: vi.fn(() => () => {}) }
})

vi.mock('features/percentileCalculator/components/TimeRangeSlider', () => ({
  TimeRangeSlider: ({ onYearRangeChange }: { onYearRangeChange: (n: number) => void }) => (
    <button type="button" data-testid="change-time-range" onClick={() => onYearRangeChange(5)}>
      Change Range
    </button>
  ),
  yearWhenTheCalculationIsDone: 2024
}))

vi.mock('features/percentileCalculator/components/WxStationDropdown', () => ({
  default: ({ onChange }: { onChange: (codes: number[]) => void }) => (
    <button type="button" data-testid="select-station" onClick={() => onChange([101])}>
      Select Station
    </button>
  )
}))

vi.mock('features/percentileCalculator/components/PercentileResults', () => ({ default: () => null }))
vi.mock('features/percentileCalculator/components/PercentileTextfield', () => ({ PercentileTextfield: () => null }))

const renderPage = (search = '') =>
  render(
    <Provider store={createTestStore()}>
      <MemoryRouter initialEntries={[`/${search}`]}>
        <PercentileCalculatorPage />
      </MemoryRouter>
    </Provider>
  )

describe('PercentileCalculatorPage', () => {
  beforeEach(() => {
    vi.mocked(fetchPercentiles).mockClear()
  })

  it('fetches percentiles on mount when station codes are in the URL', async () => {
    renderPage('?codes=101,202')

    await waitFor(() => {
      expect(fetchPercentiles).toHaveBeenCalledOnce()
      expect(fetchPercentiles).toHaveBeenCalledWith([101, 202], 90, expect.any(Object))
    })
  })

  it('does not fetch percentiles again when the time range slider changes', async () => {
    renderPage('?codes=101')

    await waitFor(() => {
      expect(fetchPercentiles).toHaveBeenCalledOnce()
    })

    fireEvent.click(screen.getByTestId('change-time-range'))

    // Allow any potential re-renders to settle
    await new Promise(resolve => setTimeout(resolve, 50))

    expect(fetchPercentiles).toHaveBeenCalledOnce()
  })

  it('uses the slider yearRange at the time Calculate is clicked, not the default', async () => {
    renderPage()

    // Change slider to timeRange=5 before selecting any station
    fireEvent.click(screen.getByTestId('change-time-range'))

    // Select a station to enable Calculate
    fireEvent.click(screen.getByTestId('select-station'))

    // Click Calculate — this navigates to ?codes=101
    fireEvent.click(screen.getByText('Calculate'))

    await waitFor(() => {
      expect(fetchPercentiles).toHaveBeenCalledWith([101], 90, {
        start: MOCKED_CURRENT_YEAR - 4, // timeRange=5 → start = 2024 - (5-1)
        end: MOCKED_CURRENT_YEAR
      })
    })
  })
})
