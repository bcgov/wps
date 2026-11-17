import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { type DailyClimatology, getDailyClimatology } from '@wps/api/climatologyAPI'
import { getStations } from '@wps/api/stationAPI'
import type { GeoJsonStation } from '@wps/types/stationTypes'
import { Provider } from 'react-redux'
import { MemoryRouter } from 'react-router-dom'
import type { Mock } from 'vitest'
import type { ClimatologyChartProps } from '@/features/climatology/components/ClimatologyChart'
import { createTestStore } from '@/test/testUtils'
import ClimatologyPage from './ClimatologyPage'

vi.mock('@wps/api/climatologyAPI', () => ({
  getDailyClimatology: vi.fn()
}))

vi.mock('@wps/api/stationAPI', async importOriginal => ({
  ...(await importOriginal<typeof import('@wps/api/stationAPI')>()),
  getStations: vi.fn()
}))

// The chart draws to a measured surface, which jsdom does not lay out. Its own tests cover it.
vi.mock('@/features/climatology/components/ClimatologyChart', async importOriginal => ({
  ...(await importOriginal<typeof import('@/features/climatology/components/ClimatologyChart')>()),
  default: ({ rows, variable, year, monthTicks, stationName }: ClimatologyChartProps) => (
    <div
      data-testid="climatology-chart"
      data-rows={rows.length}
      data-variable={variable}
      data-year={year}
      data-months={monthTicks.length}
      data-station={stationName}
    />
  )
}))

const station = (code: number, name: string): GeoJsonStation => ({
  type: 'Feature',
  properties: {
    code,
    name,
    ecodivision_name: null,
    core_season: { start_month: 5, start_day: 1, end_month: 9, end_day: 15 }
  },
  geometry: { type: 'Point', coordinates: [-120, 50] }
})

const currentYear = new Date().getFullYear()

const climatology = (overrides: Partial<DailyClimatology> = {}): DailyClimatology => ({
  station_code: 322,
  variable: 'temperature',
  year: currentYear,
  first_reference_year: 1990,
  last_reference_year: currentYear - 1,
  days: [
    { month: 1, day: 15, count: 30, minimum: -20, p25: -8, median: -3, p75: 1, p90: 4, maximum: 9 },
    { month: 7, day: 1, count: 30, minimum: 8, p25: 17, median: 22, p75: 27, p90: 31, maximum: 38 }
  ],
  observations: [{ date: `${currentYear}-07-01`, value: 29 }],
  ...overrides
})

const renderPage = () =>
  render(
    <Provider store={createTestStore()}>
      <MemoryRouter>
        <ClimatologyPage />
      </MemoryRouter>
    </Provider>
  )

const chooseStation = async (label: string) => {
  const input = await screen.findByLabelText('Weather station')
  fireEvent.change(input, { target: { value: label.slice(0, 3) } })
  fireEvent.click(await screen.findByText(label))
}

const chooseOption = async (label: string, option: string) => {
  fireEvent.mouseDown(screen.getByLabelText(label))
  fireEvent.click(await within(await screen.findByRole('listbox')).findByText(option))
}

describe('ClimatologyPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    ;(getStations as Mock).mockResolvedValue([station(322, 'AFTON'), station(209, 'ALEXIS CREEK')])
    ;(getDailyClimatology as Mock).mockResolvedValue(climatology())
  })

  it('asks for a station before loading anything', async () => {
    renderPage()

    expect(await screen.findByText(/Choose a weather station/)).toBeInTheDocument()
    expect(getDailyClimatology).not.toHaveBeenCalled()
    expect(screen.queryByTestId('climatology-chart')).not.toBeInTheDocument()
  })

  it('charts the chosen station for temperature in the current year, April to October', async () => {
    renderPage()

    await chooseStation('AFTON (322)')

    const chart = await screen.findByTestId('climatology-chart')
    expect(getDailyClimatology).toHaveBeenCalledWith(322, 'temperature', currentYear)
    expect(chart).toHaveAttribute('data-station', 'AFTON')
    expect(chart).toHaveAttribute('data-variable', 'temperature')
    // Only the July day is in the fire season months.
    expect(chart).toHaveAttribute('data-rows', '1')
    expect(chart).toHaveAttribute('data-months', '7')
    expect(screen.getByText(`AFTON: daily temperature, ${currentYear}`)).toBeInTheDocument()
    expect(screen.getByText(new RegExp(`compared with 1990 to ${currentYear - 1}`))).toBeInTheDocument()
    expect(screen.getByTestId('climatology-legend')).toBeInTheDocument()
  })

  it('shows every month for the full year', async () => {
    renderPage()
    await chooseStation('AFTON (322)')
    await screen.findByTestId('climatology-chart')

    fireEvent.click(screen.getByRole('button', { name: 'Full year' }))

    const chart = screen.getByTestId('climatology-chart')
    expect(chart).toHaveAttribute('data-rows', '2')
    expect(chart).toHaveAttribute('data-months', '12')
    // The months shown change what is drawn, not what is fetched.
    expect(getDailyClimatology).toHaveBeenCalledTimes(1)
  })

  it('loads again when the variable or year changes', async () => {
    renderPage()
    await chooseStation('AFTON (322)')
    await screen.findByTestId('climatology-chart')

    await chooseOption('Variable', 'Relative humidity')
    await waitFor(() => expect(getDailyClimatology).toHaveBeenLastCalledWith(322, 'relative_humidity', currentYear))

    await chooseOption('Year', `${currentYear - 1}`)
    await waitFor(() => expect(getDailyClimatology).toHaveBeenLastCalledWith(322, 'relative_humidity', currentYear - 1))
  })

  it('says so when the station has no history for the months shown', async () => {
    ;(getDailyClimatology as Mock).mockResolvedValue(climatology({ days: [], observations: [] }))
    renderPage()

    await chooseStation('AFTON (322)')

    expect(await screen.findByText(/AFTON has no history of daily temperature/)).toBeInTheDocument()
    expect(screen.queryByTestId('climatology-chart')).not.toBeInTheDocument()
  })

  it('reports a failed load', async () => {
    ;(getDailyClimatology as Mock).mockRejectedValue(new Error('Request failed'))
    renderPage()

    await chooseStation('AFTON (322)')

    expect(await screen.findByText('The climatology for this station could not be loaded.')).toBeInTheDocument()
    expect(screen.queryByTestId('climatology-chart')).not.toBeInTheDocument()
  })
})
