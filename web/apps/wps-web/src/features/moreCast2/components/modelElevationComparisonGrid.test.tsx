import type { DataGridProProps } from '@mui/x-data-grid-pro'
import { configureStore } from '@reduxjs/toolkit'
import { act, render, screen, waitFor, within } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import { fetchWeatherIndeterminates, WeatherDeterminate, type WeatherIndeterminate } from '@wps/api/moreCast2API'
import {
  getStationGroups,
  getStationGroupsMembers,
  type StationGroup,
  type StationGroupMember
} from '@wps/api/stationAPI'
import rootReducer from 'app/rootReducer'
import { DateTime } from 'luxon'
import { Provider } from 'react-redux'
import { describe, vi } from 'vitest'
import { MorecastDraftForecast } from '../forecastDraft'
import * as modelElevation from '../modelElevation'
import MoreCast2Page from '../pages/MoreCast2Page'
import { getWeatherIndeterminatesSuccess } from '../slices/dataSlice'
import { selectedStationsChanged } from '../slices/selectedStationsSlice'
import * as morecastUtil from '../util'
import { rowIDHasher } from '../util'
import { DataGridColumns } from './DataGridColumns'

vi.mock('@wps/api/stationAPI', async importOriginal => ({
  ...(await importOriginal<typeof import('@wps/api/stationAPI')>()),
  getStationGroups: vi.fn(),
  getStationGroupsMembers: vi.fn()
}))
vi.mock('@wps/api/moreCast2API', async importOriginal => ({
  ...(await importOriginal<typeof import('@wps/api/moreCast2API')>()),
  fetchWeatherIndeterminates: vi.fn()
}))
vi.mock('@mui/x-data-grid-pro', async importOriginal => {
  const actual = await importOriginal<typeof import('@mui/x-data-grid-pro')>()
  return {
    ...actual,
    DataGridPro: (props: DataGridProProps) => <actual.DataGridPro {...props} disableVirtualization />
  }
})

const group: StationGroup = {
  id: '1',
  display_label: 'Comparison group',
  group_description: null,
  group_owner_user_id: 'forecaster',
  group_owner_user_guid: '1'
}
const stations: StationGroupMember[] = ['Alpha station', 'Beta station'].map((name, index) => ({
  id: String(index + 1),
  station_code: index + 1,
  display_label: name,
  elevation: 900 + index * 300,
  station_status: 'ACTIVE',
  fire_centre: { id: '1', display_label: 'Centre' },
  fire_zone: { id: '1', display_label: 'Zone', fire_centre: '1' }
}))
const forecastDate = DateTime.utc().plus({ days: 1 }).startOf('day').set({ hour: 20 })
const predictions: WeatherIndeterminate[] = stations.map(station => ({
  id: String(station.station_code),
  station_code: station.station_code,
  station_name: station.display_label,
  determinate: WeatherDeterminate.HRDPS,
  utc_timestamp: forecastDate.toISO()!,
  prediction_run_timestamp: forecastDate.minus({ days: 1 }).startOf('day').toISO()!,
  model_elevation: station.station_code === 1 ? 850.4 : 1000,
  latitude: 50,
  longitude: -120,
  temperature: 20,
  relative_humidity: 40,
  precipitation: 0,
  wind_direction: 180,
  wind_speed: 10,
  grass_curing: 60,
  fine_fuel_moisture_code: null,
  duff_moisture_code: null,
  drought_code: null,
  initial_spread_index: null,
  build_up_index: null,
  fire_weather_index: null,
  danger_rating: null
}))

const renderPage = async () => {
  vi.mocked(getStationGroups).mockResolvedValue([group])
  vi.mocked(getStationGroupsMembers).mockResolvedValue(stations)
  vi.mocked(fetchWeatherIndeterminates).mockResolvedValue({
    actuals: [],
    grassCuring: [],
    predictions,
    forecasts: predictions.map(row => ({ ...row, determinate: WeatherDeterminate.FORECAST, temperature: null }))
  })
  const store = configureStore({ reducer: rootReducer })
  const result = render(
    <Provider store={store}>
      <MoreCast2Page />
    </Provider>
  )
  await userEvent.click(await screen.findByRole('combobox'))
  await userEvent.click(await screen.findByRole('option', { name: 'Comparison group' }))
  await screen.findByRole('button', { name: 'Compare model elevations for Alpha station' })
  await userEvent.click(
    within(screen.getByTestId('morecast2-station-panel')).getByText('Beta station', { exact: true })
  )
  await screen.findByRole('button', { name: 'Compare model elevations for Beta station' })
  return { store, ...result }
}
const compare = (name = 'Alpha station') => screen.getByRole('button', { name: `Compare model elevations for ${name}` })
const panel = (name = 'Alpha station') => screen.getByRole('region', { name: `Model elevations for ${name}` })
const cell = (code: number, field = 'tempForecast'): HTMLElement =>
  document.querySelector<HTMLElement>(`[data-id="${rowIDHasher(code, forecastDate)}"] [data-field="${field}"]`)!

describe('station elevation comparison sidebar', { timeout: 15000 }, () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
    // keep this fixture to one day because virtualization is disabled
    const date = DateTime.fromObject({
      year: forecastDate.year,
      month: forecastDate.month,
      day: forecastDate.day
    }).toJSDate()
    vi.spyOn(morecastUtil, 'getDefaultDateRange').mockReturnValue({ startDate: date, endDate: date })
  })
  afterEach(() => {
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it('fills a station draft from the selected chart model', async () => {
    await renderPage()
    await userEvent.click(screen.getByRole('button', { name: 'Compare model elevations for Alpha station' }))
    await userEvent.click(within(panel()).getByRole('button', { name: 'HRDPS' }))
    await userEvent.clear(screen.getByRole('spinbutton', { name: 'Lapse rate (°C/km)' }))
    await userEvent.type(screen.getByRole('spinbutton', { name: 'Lapse rate (°C/km)' }), '9.8')
    await userEvent.click(screen.getByRole('button', { name: 'Fill temperature forecasts' }))
    expect(screen.getByRole('status')).toHaveTextContent('Filled temperature forecasts')
    // the grid displays whole degrees, while the draft retains the adjustment's precision
    await waitFor(() => expect(within(cell(1)).getByRole('textbox')).toHaveValue('20'))
    expect(
      new MorecastDraftForecast(localStorage)
        .getStoredDraftForecasts()
        ?.rows.find(row => row.stationCode === 1 && row.forDate.toISODate() === forecastDate.toISODate())?.tempForecast
        ?.value
    ).toBe(19.5)
  })

  it('opens in the sidebar without changing drafts, columns, or requests', async () => {
    await renderPage()
    await userEvent.click(cell(2))
    expect(screen.queryByRole('region', { name: /Model elevations for/ })).not.toBeInTheDocument()
    const columns = vi.spyOn(DataGridColumns, 'getTabColumns')
    const requests = vi.mocked(fetchWeatherIndeterminates).mock.calls.length
    const draft = localStorage.getItem('morecastForecastDraft')
    await userEvent.click(compare())
    expect(screen.getByTestId('morecast2-station-panel')).not.toBeVisible()
    expect(screen.queryByRole('combobox')).not.toBeInTheDocument()
    expect(panel()).toBeVisible()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(localStorage.getItem('morecastForecastDraft')).toBe(draft)
    expect(fetchWeatherIndeterminates).toHaveBeenCalledTimes(requests)
    expect(columns).not.toHaveBeenCalled()
    await userEvent.click(within(panel()).getByRole('button', { name: 'Close elevation comparison' }))
    expect(screen.queryByRole('region', { name: 'Model elevations for Alpha station' })).not.toBeInTheDocument()
    expect(screen.getByTestId('morecast2-station-panel')).toBeVisible()
  })

  it('follows forecast station clicks while editing, copying models, and switching tabs', async () => {
    await renderPage()
    await userEvent.click(compare())
    const metadata = vi.spyOn(modelElevation, 'getModelElevationData')
    await userEvent.dblClick(cell(2))
    const input = within(cell(2)).getByRole('spinbutton')
    await userEvent.clear(input)
    await userEvent.type(input, '25{Enter}')
    await waitFor(() => expect(within(cell(2)).getByRole('textbox')).toHaveValue('25'))
    expect(panel('Beta station')).toBeInTheDocument()
    expect(
      new MorecastDraftForecast(localStorage)
        .getStoredDraftForecasts()
        ?.rows.find(row => row.stationCode === 2 && row.forDate.toISODate() === forecastDate.toISODate())?.tempForecast
        ?.value
    ).toBe(25)
    await userEvent.click(within(panel('Beta station')).getByRole('button', { name: 'HRDPS' }))
    const rate = screen.getByRole('spinbutton', { name: 'Lapse rate (°C/km)' })
    await userEvent.type(rate, '6.5')
    await userEvent.dblClick(cell(2, 'tempHRDPS'))
    expect(rate).toHaveValue(6.5)
    await waitFor(() => expect(within(cell(2)).getByRole('textbox')).toHaveValue('20'))
    await userEvent.click(screen.getByTestId('rh-tab-button-unselected'))
    expect(panel('Beta station')).toBeInTheDocument()
    await userEvent.click(screen.getByTestId('summary-tab-button-unselected'))
    expect(panel('Beta station')).toBeInTheDocument()
    expect(panel('Beta station')).toBeVisible()
    await userEvent.click(cell(1))
    expect(panel()).toBeVisible()
    await userEvent.click(cell(2))
    expect(panel('Beta station')).toBeVisible()
    await userEvent.click(screen.getByTestId('temp-tab-button-unselected'))
    expect(panel('Beta station')).toBeInTheDocument()
    expect(metadata).not.toHaveBeenCalled()
    await userEvent.click(compare('Beta station'))
    expect(within(panel('Beta station')).getByText('-200')).toBeInTheDocument()
  })

  it('fills only the station followed by the open panel', async () => {
    await renderPage()
    await userEvent.click(compare())
    await userEvent.click(cell(2, 'tempHRDPS'))
    await userEvent.click(within(panel('Beta station')).getByRole('button', { name: 'HRDPS' }))
    await userEvent.type(screen.getByRole('spinbutton', { name: 'Lapse rate (°C/km)' }), '9.8')
    await userEvent.click(screen.getByRole('button', { name: 'Fill temperature forecasts' }))
    const draft = new MorecastDraftForecast(localStorage).getStoredDraftForecasts()
    expect(draft?.rows.every(row => row.stationCode === 2)).toBe(true)
    expect(draft?.rows.find(row => row.stationCode === 2)?.tempForecast?.value).toBe(18)
    expect(within(cell(1)).getByRole('textbox')).toHaveValue('')
  })

  it('ignores elevation headers and observed rows while the panel is open', async () => {
    const { store } = await renderPage()
    await userEvent.click(compare())
    const header = compare('Beta station').closest('[role="row"]')!
    await userEvent.click(header.querySelector<HTMLElement>('[data-field="tempHRDPS"]')!)
    expect(panel()).toBeVisible()
    const weather = store.getState().weatherIndeterminates
    act(() =>
      store.dispatch(
        getWeatherIndeterminatesSuccess({
          actuals: [
            {
              ...weather.predictions.find(row => row.station_code === 2)!,
              determinate: WeatherDeterminate.ACTUAL,
              temperature: 21
            }
          ],
          predictions: weather.predictions,
          forecasts: weather.forecasts,
          grassCuring: weather.grassCuring
        })
      )
    )
    await userEvent.click(cell(2))
    expect(panel()).toBeVisible()
    await userEvent.click(screen.getByTestId('summary-tab-button-unselected'))
    await userEvent.click(cell(2))
    expect(panel()).toBeVisible()
  })

  it('supports keyboard activation and keeps Escape available for forecast editing', async () => {
    await renderPage()
    const button = compare()
    act(() => button.focus())
    await userEvent.keyboard(' ')
    expect(panel()).toBeInTheDocument()
    await userEvent.dblClick(cell(1))
    await userEvent.keyboard('{Escape}')
    expect(within(cell(1)).queryByRole('spinbutton')).not.toBeInTheDocument()
    expect(panel()).toBeInTheDocument()
  })

  it('refreshes the comparison from the same elevations as the grid headers', async () => {
    const { store } = await renderPage()
    await userEvent.click(compare())
    const weather = store.getState().weatherIndeterminates
    act(() =>
      store.dispatch(
        getWeatherIndeterminatesSuccess({
          actuals: weather.actuals,
          forecasts: weather.forecasts,
          grassCuring: weather.grassCuring,
          predictions: weather.predictions.map(row => ({ ...row, model_elevation: 1120 }))
        })
      )
    )
    expect(within(panel()).getByText('1120')).toBeInTheDocument()
    expect(within(panel()).getByText('+220')).toBeInTheDocument()
  })

  it('closes when its station is deselected and stays closed if it is selected again', async () => {
    const { store } = await renderPage()
    await userEvent.click(compare())
    const sidebar = screen.getByTestId('morecast2-station-panel')
    act(() => store.dispatch(selectedStationsChanged([stations[1]])))
    expect(screen.queryByRole('region', { name: 'Model elevations for Alpha station' })).not.toBeInTheDocument()
    await userEvent.click(within(sidebar).getByText('Alpha station', { exact: true }))
    expect(compare()).toBeInTheDocument()
    expect(screen.queryByRole('region', { name: 'Model elevations for Alpha station' })).not.toBeInTheDocument()
  })
})
