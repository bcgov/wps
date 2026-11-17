import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import {
  type ClimatologySeries,
  type DailyClimatology,
  getClimatologyFireCentres,
  getDailyClimatology
} from '@wps/api/climatologyAPI'
import { getStationGroups, getStationGroupsMembers, getStations } from '@wps/api/stationAPI'
import type { GeoJsonStation } from '@wps/types/stationTypes'
import { Provider } from 'react-redux'
import { MemoryRouter } from 'react-router-dom'
import type { Mock } from 'vitest'
import type { ClimatologyChartProps } from '@/features/climatology/components/ClimatologyChart'
import type { ClimatologyTimelineProps } from '@/features/climatology/components/ClimatologyTimeline'
import { createTestStore } from '@/test/testUtils'
import ClimatologyPage, { MAX_STATIONS } from './ClimatologyPage'

vi.mock('@wps/api/climatologyAPI', () => ({
  getDailyClimatology: vi.fn(),
  getClimatologyFireCentres: vi.fn()
}))

vi.mock('@wps/api/stationAPI', async importOriginal => ({
  ...(await importOriginal<typeof import('@wps/api/stationAPI')>()),
  getStations: vi.fn(),
  getStationGroups: vi.fn(),
  getStationGroupsMembers: vi.fn()
}))

// The charts draw to a measured surface, which jsdom does not lay out. Their own tests cover
// them. The stand-ins show what they were given and can propose new dates.
const currentYear = new Date().getFullYear()
const JULY_1 = Date.UTC(currentYear, 6, 1)
const JULY_2 = Date.UTC(currentYear, 6, 2)
const isoWindow = ({ start, end }: { start: number; end: number }) =>
  `${new Date(start).toISOString().slice(0, 10)}/${new Date(end).toISOString().slice(0, 10)}`

vi.mock('@/features/climatology/components/ClimatologyChart', async importOriginal => ({
  ...(await importOriginal<typeof import('@/features/climatology/components/ClimatologyChart')>()),
  default: ({ rows, variable, year, dateWindow, onDateWindowChange, title, yDomain }: ClimatologyChartProps) => (
    <div
      data-testid="climatology-chart"
      data-rows={rows.length}
      data-variable={variable}
      data-year={year}
      data-window={isoWindow(dateWindow)}
      data-title={title}
      data-y-domain={yDomain ? yDomain.join('/') : 'own'}
    >
      <button type="button" onClick={() => onDateWindowChange({ start: JULY_1, end: JULY_2 })}>
        Zoom to July 1 and 2
      </button>
    </div>
  )
}))

vi.mock('@/features/climatology/components/ClimatologyTimeline', () => ({
  default: ({ dateWindow }: ClimatologyTimelineProps) => (
    <div data-testid="climatology-timeline" data-window={isoWindow(dateWindow)} />
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

const day = (month: number, dayOfMonth: number, minimum = 8, maximum = 38) => ({
  month,
  day: dayOfMonth,
  count: 30,
  station_count: 1,
  minimum,
  p25: 17,
  median: 22,
  p75: 27,
  p90: 31,
  maximum
})

const series = (codes: number[], overrides: Partial<ClimatologySeries> = {}): ClimatologySeries => ({
  station_codes: codes,
  first_reference_year: 1990,
  last_reference_year: currentYear - 1,
  days: [day(1, 15, -20, 9), day(7, 1), day(7, 2), day(10, 31, 0, 20)],
  observations: [{ date: `${currentYear}-07-01`, value: 29, station_count: codes.length }],
  ...overrides
})

const climatology = (overrides: Partial<DailyClimatology> = {}): DailyClimatology => ({
  variable: 'temperature',
  year: currentYear,
  method: 'average',
  series: [series([322])],
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
  const input = await screen.findByLabelText('Weather stations')
  fireEvent.change(input, { target: { value: label.slice(0, 3) } })
  fireEvent.click(await screen.findByText(label))
}

const chooseGroup = async (label: string) => {
  const input = screen.getByLabelText('Station group')
  fireEvent.change(input, { target: { value: label.slice(0, 4) } })
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
    ;(getStationGroups as Mock).mockResolvedValue([
      {
        id: 'g1',
        display_label: 'My valleys',
        group_description: null,
        group_owner_user_guid: '',
        group_owner_user_id: ''
      }
    ])
    ;(getStationGroupsMembers as Mock).mockResolvedValue([
      {
        id: '1',
        display_label: 'ALEXIS CREEK',
        fire_centre: { id: '1', display_label: '' },
        fire_zone: null,
        station_code: 209,
        station_status: 'ACTIVE'
      }
    ])
    ;(getClimatologyFireCentres as Mock).mockResolvedValue([
      {
        id: 2,
        name: 'Kamloops Fire Centre',
        stations: [
          { code: 322, name: 'AFTON', zone: 'K2' },
          { code: 209, name: 'ALEXIS CREEK', zone: 'K4' }
        ]
      }
    ])
    ;(getDailyClimatology as Mock).mockResolvedValue(climatology())
  })

  it('asks for stations before loading anything', async () => {
    renderPage()

    expect(await screen.findByText(/Choose weather stations, or a fire centre/)).toBeInTheDocument()
    expect(getDailyClimatology).not.toHaveBeenCalled()
    expect(screen.queryByTestId('climatology-chart')).not.toBeInTheDocument()
  })

  it('charts one station for temperature in the current year, April to October', async () => {
    renderPage()

    await chooseStation('AFTON (322)')

    const chart = await screen.findByTestId('climatology-chart')
    expect(getDailyClimatology).toHaveBeenCalledWith([322], 'temperature', currentYear, 'average')
    expect(chart).toHaveAttribute('data-title', 'AFTON')
    // The January day is outside the fire season months.
    expect(chart).toHaveAttribute('data-rows', '3')
    expect(chart).toHaveAttribute('data-window', `${currentYear}-07-01/${currentYear}-10-31`)
    expect(chart).toHaveAttribute('data-y-domain', 'own')
    expect(screen.getByText(`AFTON: daily temperature, ${currentYear}`)).toBeInTheDocument()
    expect(screen.getByText(new RegExp(`compared with 1990 to ${currentYear - 1}`))).toBeInTheDocument()
    expect(screen.getByTestId('climatology-legend')).toHaveTextContent(`${currentYear}Historical median`)
    // One station is not combined, so there is nothing to choose.
    expect(screen.queryByRole('button', { name: 'Pooled' })).not.toBeInTheDocument()
  })

  it('charts a fire centre as the mean of its stations', async () => {
    ;(getDailyClimatology as Mock).mockResolvedValue(climatology({ series: [series([322, 209])] }))
    renderPage()

    await chooseGroup('Kamloops Fire Centre')

    const chart = await screen.findByTestId('climatology-chart')
    expect(getDailyClimatology).toHaveBeenCalledWith([322, 209], 'temperature', currentYear, 'average')
    expect(chart).toHaveAttribute('data-title', 'Kamloops Fire Centre')
    expect(screen.getByText(`Kamloops Fire Centre: daily temperature, ${currentYear}`)).toBeInTheDocument()
    expect(screen.getByText(/Each day is the mean of the stations/)).toBeInTheDocument()
    expect(screen.getByTestId('climatology-legend')).toHaveTextContent(`${currentYear} (mean of stations)`)
    expect(screen.getByRole('button', { name: 'Average' })).toHaveAttribute('aria-pressed', 'true')
  })

  it('charts a fire zone', async () => {
    renderPage()

    await chooseGroup('K2, Kamloops Fire Centre')

    await waitFor(() => expect(getDailyClimatology).toHaveBeenCalledWith([322], 'temperature', currentYear, 'average'))
  })

  it('fetches the stations of a saved group when it is chosen', async () => {
    renderPage()

    await chooseGroup('My valleys')

    await waitFor(() => expect(getStationGroupsMembers).toHaveBeenCalledWith(['g1']))
    await waitFor(() => expect(getDailyClimatology).toHaveBeenCalledWith([209], 'temperature', currentYear, 'average'))
  })

  it('pools the stations when asked', async () => {
    renderPage()
    await chooseGroup('Kamloops Fire Centre')
    await screen.findByTestId('climatology-chart')

    fireEvent.click(screen.getByRole('button', { name: 'Pooled' }))

    await waitFor(() =>
      expect(getDailyClimatology).toHaveBeenLastCalledWith([322, 209], 'temperature', currentYear, 'pooled')
    )
    expect(screen.getByText(/spread of every station’s values/)).toBeInTheDocument()
  })

  it('charts each station on one shared scale', async () => {
    renderPage()
    await chooseGroup('Kamloops Fire Centre')
    await screen.findByTestId('climatology-chart')
    ;(getDailyClimatology as Mock).mockResolvedValue(
      climatology({
        method: 'each',
        series: [series([322]), series([209], { days: [day(7, 1, -5, 45)] })]
      })
    )

    fireEvent.click(screen.getByRole('button', { name: 'Each station' }))

    await waitFor(() => expect(screen.getAllByTestId('climatology-chart')).toHaveLength(2))
    expect(getDailyClimatology).toHaveBeenLastCalledWith([322, 209], 'temperature', currentYear, 'each')
    const [afton, alexis] = screen.getAllByTestId('climatology-chart')
    expect(afton).toHaveAttribute('data-title', 'AFTON')
    expect(alexis).toHaveAttribute('data-title', 'ALEXIS CREEK')
    // Both share the lowest and highest of either station, 1 July's -5 to 45.
    expect(afton).toHaveAttribute('data-y-domain', '-5/45')
    expect(alexis).toHaveAttribute('data-y-domain', '-5/45')
    expect(screen.getAllByRole('heading', { level: 3 }).map(heading => heading.textContent)).toEqual([
      'AFTON (322)',
      'ALEXIS CREEK (209)'
    ])
    expect(screen.getByTestId('climatology-legend')).toHaveTextContent(`${currentYear}Historical median`)
  })

  it('forgets the group when its stations are edited', async () => {
    renderPage()
    await chooseGroup('Kamloops Fire Centre')
    await screen.findByTestId('climatology-chart')

    fireEvent.click(within(screen.getByRole('button', { name: 'AFTON (322)' })).getByTestId('CancelIcon'))

    await waitFor(() =>
      expect(getDailyClimatology).toHaveBeenLastCalledWith([209], 'temperature', currentYear, 'average')
    )
    expect(screen.getByLabelText('Station group')).toHaveValue('')
  })

  it('does not load more stations than the API combines', async () => {
    ;(getClimatologyFireCentres as Mock).mockResolvedValue([
      {
        id: 1,
        name: 'Big Fire Centre',
        stations: Array.from({ length: MAX_STATIONS + 1 }, (_, index) => ({
          code: index,
          name: `S${index}`,
          zone: null
        }))
      }
    ])
    renderPage()

    await chooseGroup('Big Fire Centre')

    expect(await screen.findByText(new RegExp(`Choose at most ${MAX_STATIONS} stations`))).toBeInTheDocument()
    expect(getDailyClimatology).not.toHaveBeenCalled()
  })

  it('still offers the groups that loaded when one list fails', async () => {
    ;(getStationGroups as Mock).mockRejectedValue(new Error('Forbidden'))
    renderPage()

    expect(await screen.findByText('Some station groups could not be loaded.')).toBeInTheDocument()
    await chooseGroup('Kamloops Fire Centre')
    expect(await screen.findByTestId('climatology-chart')).toBeInTheDocument()
  })

  it('shows every month for the full year without loading again', async () => {
    renderPage()
    await chooseStation('AFTON (322)')
    await screen.findByTestId('climatology-chart')

    fireEvent.click(screen.getByRole('button', { name: 'Full year' }))

    const chart = screen.getByTestId('climatology-chart')
    expect(chart).toHaveAttribute('data-rows', '4')
    expect(chart).toHaveAttribute('data-window', `${currentYear}-01-15/${currentYear}-10-31`)
    expect(getDailyClimatology).toHaveBeenCalledTimes(1)
  })

  it('loads again when the variable or year changes', async () => {
    renderPage()
    await chooseStation('AFTON (322)')
    await screen.findByTestId('climatology-chart')

    await chooseOption('Variable', 'Relative humidity')
    await waitFor(() =>
      expect(getDailyClimatology).toHaveBeenLastCalledWith([322], 'relative_humidity', currentYear, 'average')
    )

    await chooseOption('Year', `${currentYear - 1}`)
    await waitFor(() =>
      expect(getDailyClimatology).toHaveBeenLastCalledWith([322], 'relative_humidity', currentYear - 1, 'average')
    )
  })

  it('shares the dates chosen on the chart with the timeline, and shows every day again on reset', async () => {
    renderPage()
    await chooseStation('AFTON (322)')
    await screen.findByTestId('climatology-chart')
    const reset = screen.getByRole('button', { name: 'Show every day' })
    expect(reset).toBeDisabled()

    fireEvent.click(screen.getByRole('button', { name: 'Zoom to July 1 and 2' }))

    const window = `${currentYear}-07-01/${currentYear}-07-02`
    expect(screen.getByTestId('climatology-chart')).toHaveAttribute('data-window', window)
    expect(screen.getByTestId('climatology-timeline')).toHaveAttribute('data-window', window)
    expect(screen.getByText('Showing Jul 1 to Jul 2')).toBeInTheDocument()

    fireEvent.click(reset)

    expect(screen.getByTestId('climatology-chart')).toHaveAttribute(
      'data-window',
      `${currentYear}-07-01/${currentYear}-10-31`
    )
    expect(reset).toBeDisabled()
  })

  it('says so when the stations have no history for the months shown', async () => {
    ;(getDailyClimatology as Mock).mockResolvedValue(
      climatology({ series: [series([322], { days: [], observations: [] })] })
    )
    renderPage()

    await chooseStation('AFTON (322)')

    expect(await screen.findByText(/AFTON has no history of daily temperature/)).toBeInTheDocument()
    expect(screen.queryByTestId('climatology-chart')).not.toBeInTheDocument()
  })

  it('reports a failed load', async () => {
    ;(getDailyClimatology as Mock).mockRejectedValue(new Error('Request failed'))
    renderPage()

    await chooseStation('AFTON (322)')

    expect(await screen.findByText('The climatology for these stations could not be loaded.')).toBeInTheDocument()
    expect(screen.queryByTestId('climatology-chart')).not.toBeInTheDocument()
  })
})
