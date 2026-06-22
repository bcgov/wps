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
    renderPage('?codes=101,202&timeRange=10')

    await waitFor(() => {
      expect(fetchPercentiles).toHaveBeenCalledOnce()
      expect(fetchPercentiles).toHaveBeenCalledWith([101, 202], 90, {
        start: MOCKED_CURRENT_YEAR - 9,
        end: MOCKED_CURRENT_YEAR
      })
    })
  })

  it('falls back to the default time range for URLs without a timeRange param', async () => {
    renderPage('?codes=101')

    await waitFor(() => {
      expect(fetchPercentiles).toHaveBeenCalledWith([101], 90, {
        start: MOCKED_CURRENT_YEAR - 9, // defaultTimeRange=10
        end: MOCKED_CURRENT_YEAR
      })
    })
  })

  it('does not fetch when the time range slider changes without clicking Calculate', async () => {
    renderPage('?codes=101&timeRange=10')

    await waitFor(() => {
      expect(fetchPercentiles).toHaveBeenCalledOnce()
    })

    fireEvent.click(screen.getByTestId('change-time-range'))

    await new Promise(resolve => setTimeout(resolve, 50))

    expect(fetchPercentiles).toHaveBeenCalledOnce()
  })

  it('fetches with the slider yearRange when Calculate is clicked', async () => {
    renderPage()

    fireEvent.click(screen.getByTestId('select-station'))
    fireEvent.click(screen.getByTestId('change-time-range')) // timeRange → 5

    fireEvent.click(screen.getByText('Calculate'))

    await waitFor(() => {
      expect(fetchPercentiles).toHaveBeenCalledWith([101], 90, {
        start: MOCKED_CURRENT_YEAR - 4, // timeRange=5
        end: MOCKED_CURRENT_YEAR
      })
    })
  })

  it('re-fetches with the updated yearRange when Calculate is clicked again', async () => {
    renderPage('?codes=101&timeRange=10')

    await waitFor(() => {
      expect(fetchPercentiles).toHaveBeenCalledOnce()
    })

    fireEvent.click(screen.getByTestId('change-time-range')) // local timeRange → 5, no fetch yet
    await new Promise(resolve => setTimeout(resolve, 50))
    expect(fetchPercentiles).toHaveBeenCalledOnce()

    fireEvent.click(screen.getByText('Calculate'))

    await waitFor(() => {
      expect(fetchPercentiles).toHaveBeenCalledTimes(2)
      expect(fetchPercentiles).toHaveBeenLastCalledWith([101], 90, {
        start: MOCKED_CURRENT_YEAR - 4, // timeRange=5
        end: MOCKED_CURRENT_YEAR
      })
    })
  })
})
