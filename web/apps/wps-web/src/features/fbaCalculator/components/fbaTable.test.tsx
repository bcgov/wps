import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { fetchFireBehaviourStations } from 'features/fbaCalculator/slices/fbaCalculatorSlice'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import { Provider } from 'react-redux'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createTestStore } from '@/test/testUtils'
import FBATable from './FBATable'

vi.mock('@wps/api/stationAPI', () => ({
  getStations: vi.fn(() => Promise.resolve([])),
  StationSource: { wildfire_one: 'wildfire_one' }
}))

vi.mock('features/stations/slices/stationsSlice', async () => {
  const actual = await vi.importActual<typeof import('features/stations/slices/stationsSlice')>(
    'features/stations/slices/stationsSlice'
  )
  return { ...actual, fetchWxStations: vi.fn(() => () => {}) }
})

vi.mock('features/fbaCalculator/slices/fbaCalculatorSlice', async () => {
  const actual = await vi.importActual<typeof import('features/fbaCalculator/slices/fbaCalculatorSlice')>(
    'features/fbaCalculator/slices/fbaCalculatorSlice'
  )
  return { ...actual, fetchFireBehaviourStations: vi.fn(() => () => {}) }
})

vi.mock('@wps/ui/WPSDatePicker', () => ({
  default: () => <div data-testid="date-picker" />
}))

vi.mock('@wps/ui/AboutDataPopover', () => ({
  default: () => <div data-testid="about-data" />
}))

vi.mock('./FilterColumnsModal', () => ({
  default: () => <div data-testid="filter-columns-modal" />
}))

const preloadedState = {
  fireWeatherStations: {
    loading: false,
    error: null,
    stations: [
      {
        type: 'Feature',
        geometry: null,
        properties: {
          code: 322,
          name: 'AFTON'
        }
      },
      {
        type: 'Feature',
        geometry: null,
        properties: {
          code: 209,
          name: 'ALEXIS CREEK'
        }
      }
    ],
    stationsByCode: {},
    selectedStationsByCode: [],
    codesOfRetrievedStationData: []
  },
  fbaCalculatorResults: {
    loading: false,
    error: null,
    fireBehaviourResultStations: [],
    date: null
  }
}

const renderTable = (search = '?s=322&f=c1&c=1') =>
  render(
    <Provider store={createTestStore(preloadedState)}>
      <MemoryRouter initialEntries={[`/${search}`]}>
        <FBATable />
      </MemoryRouter>
    </Provider>
  )

const getInput = (testId: string) => screen.getByTestId(testId).querySelector('input') as HTMLInputElement

describe('FBATable', () => {
  beforeEach(() => {
    vi.mocked(fetchWxStations).mockClear()
    vi.mocked(fetchFireBehaviourStations).mockClear()
  })

  it('resets adjusted weather values for selected rows', async () => {
    renderTable()

    await waitFor(() => {
      expect(screen.getByTestId('precipInput-fba-0')).toBeInTheDocument()
    })

    fireEvent.change(getInput('precipInput-fba-0'), { target: { value: '7' } })
    fireEvent.blur(getInput('precipInput-fba-0'))
    fireEvent.change(getInput('windSpeedInput-fba-0'), { target: { value: '12' } })
    fireEvent.blur(getInput('windSpeedInput-fba-0'))

    await waitFor(() => {
      expect(fetchFireBehaviourStations).toHaveBeenCalledWith(expect.anything(), [
        expect.objectContaining({ id: 0, precip: 7, windSpeed: 12 })
      ])
    })

    fireEvent.click(within(screen.getByTestId('selection-checkbox-fba')).getByRole('checkbox'))
    fireEvent.click(screen.getByTestId('reset-selected-btn'))
    fireEvent.click(screen.getByTestId('reset-dialog-confirm-button'))

    await waitFor(() => {
      expect(fetchFireBehaviourStations).toHaveBeenLastCalledWith(expect.anything(), [
        expect.objectContaining({ id: 0, precip: undefined, windSpeed: undefined })
      ])
    })
  })

  it('removes selected rows from the table', async () => {
    renderTable('?s=322&f=c1&c=1,s=209&f=c2&c=2')

    await waitFor(() => {
      expect(screen.getByTestId('precipInput-fba-0')).toBeInTheDocument()
      expect(screen.getByTestId('precipInput-fba-1')).toBeInTheDocument()
    })

    const firstRow = screen.getByTestId('precipInput-fba-0').closest('tr') as HTMLTableRowElement
    const firstRowCheckbox = within(firstRow).getByRole('checkbox')
    fireEvent.click(firstRowCheckbox)
    await waitFor(() => {
      expect(firstRowCheckbox).toBeChecked()
    })

    fireEvent.click(screen.getByTestId('remove-rows'))

    await waitFor(() => {
      expect(screen.getAllByTestId(/precipInput-fba-/)).toHaveLength(1)
    })
  })
})
