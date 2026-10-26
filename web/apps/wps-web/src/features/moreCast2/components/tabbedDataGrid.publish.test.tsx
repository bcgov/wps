import { configureStore } from '@reduxjs/toolkit'
import { act, render, screen, waitFor } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import { fetchWeatherIndeterminates, submitMoreCastForecastRecords, WeatherDeterminate } from '@wps/api/moreCast2API'
import rootReducer from 'app/rootReducer'
import { ROLES } from 'features/auth/roles'
import { MorecastDraftForecast } from 'features/moreCast2/forecastDraft'
import {
  getWeatherIndeterminates,
  getWeatherIndeterminatesSuccess,
  selectAllMoreCast2Rows
} from 'features/moreCast2/slices/dataSlice'
import { selectedStationsChanged } from 'features/moreCast2/slices/selectedStationsSlice'
import { rowIDHasher } from 'features/moreCast2/util'
import { DateTime } from 'luxon'
import { Provider } from 'react-redux'
import { vi } from 'vitest'
import TabbedDataGrid from './TabbedDataGrid'

vi.mock('@wps/api/moreCast2API', async importOriginal => ({
  ...(await importOriginal<typeof import('@wps/api/moreCast2API')>()),
  submitMoreCastForecastRecords: vi.fn(),
  fetchWeatherIndeterminates: vi.fn()
}))

const timestamp = DateTime.utc(2030, 7, 4, 20)
const skipped = [{ station_code: 1, station_name: 'Test station', for_date: timestamp.toMillis() }]

const createPublishingStore = () => {
  const initial = rootReducer(undefined, { type: 'test' })
  return configureStore({
    reducer: rootReducer,
    preloadedState: {
      ...initial,
      authentication: {
        ...initial.authentication,
        isAuthenticated: true,
        roles: [ROLES.MORECAST_2.WRITE_FORECAST]
      },
      selectedStations: {
        selectedStations: [
          {
            id: '1',
            display_label: 'Test station',
            station_code: 1,
            station_status: 'ACTIVE',
            fire_centre: { id: '1', display_label: 'Centre' },
            fire_zone: { id: '1', display_label: 'Zone', fire_centre: '1' }
          }
        ]
      },
      weatherIndeterminates: {
        ...initial.weatherIndeterminates,
        forecasts: [
          {
            id: '1',
            station_code: 1,
            station_name: 'Test station',
            determinate: WeatherDeterminate.FORECAST,
            utc_timestamp: timestamp.toISO()!,
            latitude: 50,
            longitude: -120,
            temperature: 20,
            relative_humidity: 40,
            precipitation: 0,
            wind_speed: 10,
            wind_direction: 180,
            grass_curing: 60,
            fine_fuel_moisture_code: null,
            duff_moisture_code: null,
            drought_code: null,
            initial_spread_index: null,
            build_up_index: null,
            fire_weather_index: null,
            danger_rating: null,
            prediction_run_timestamp: null
          }
        ]
      }
    }
  })
}

const renderPublishing = async (refresh = vi.fn()) => {
  localStorage.clear()
  const testStore = createPublishingStore()
  const draft = new MorecastDraftForecast(localStorage)
  draft.createStoredForecast(selectAllMoreCast2Rows(testStore.getState()), DateTime.now())
  render(
    <Provider store={testStore}>
      <TabbedDataGrid fromTo={{}} setFromTo={vi.fn()} fetchWeatherIndeterminates={refresh} />
    </Provider>
  )
  await userEvent.click(screen.getByTestId('summary-tab-button-unselected'))
  await waitFor(() => expect(screen.getByRole('button', { name: 'Publish to WF1' })).toBeEnabled())
  await userEvent.click(screen.getByRole('button', { name: 'Publish to WF1' }))
  return { draft, refresh }
}

describe('MoreCast publishing', () => {
  afterEach(() => {
    localStorage.clear()
    vi.restoreAllMocks()
  })

  test('clears saved drafts before refreshing and shows skipped rows', async () => {
    vi.mocked(submitMoreCastForecastRecords).mockResolvedValue({
      success: true,
      wf1PublishedCount: 0,
      wf1Skipped: skipped
    })
    const refresh = vi.fn(() => {
      expect(new MorecastDraftForecast(localStorage).hasDraftForecastStored()).toBe(false)
    })
    const { draft } = await renderPublishing(refresh)
    expect(await screen.findByRole('dialog', { name: 'Forecasts saved' })).toHaveTextContent('Published 0 to WF1.')
    expect(screen.getByRole('table', { name: 'Forecasts saved only in MoreCast' })).toHaveTextContent('Test station')
    expect(draft.hasDraftForecastStored()).toBe(false)
    await waitFor(() => expect(refresh).toHaveBeenCalledTimes(1))
  })

  test('keeps the successful result if refresh fails', async () => {
    vi.mocked(submitMoreCastForecastRecords).mockResolvedValue({
      success: true,
      wf1PublishedCount: 0,
      wf1Skipped: skipped
    })
    const error = vi.spyOn(console, 'error').mockImplementation(() => {})
    const { draft } = await renderPublishing(vi.fn().mockRejectedValue(new Error('refresh failed')))
    expect(await screen.findByRole('dialog', { name: 'Forecasts saved' })).toBeVisible()
    await waitFor(() =>
      expect(error).toHaveBeenCalledWith('Could not refresh MoreCast after publishing', expect.any(Error))
    )
    expect(draft.hasDraftForecastStored()).toBe(false)
  })

  test('keeps drafts and does not refresh when publishing fails', async () => {
    vi.mocked(submitMoreCastForecastRecords).mockResolvedValue({ success: false, errorMessage: 'WF1 unavailable' })
    const { draft, refresh } = await renderPublishing()
    expect(await screen.findByRole('alert')).toHaveTextContent('WF1 unavailable')
    expect(draft.hasDraftForecastStored()).toBe(true)
    expect(refresh).not.toHaveBeenCalled()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  test('shows normal success when every forecast publishes', async () => {
    vi.mocked(submitMoreCastForecastRecords).mockResolvedValue({ success: true, wf1PublishedCount: 1, wf1Skipped: [] })
    const { draft, refresh } = await renderPublishing()
    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Forecast was successfully saved and sent to Wildfire One.'
    )
    expect(draft.hasDraftForecastStored()).toBe(false)
    expect(refresh).not.toHaveBeenCalled()
  })

  test('reconciles an actual on refresh and clears the final draft after publishing', async () => {
    localStorage.clear()
    const store = createPublishingStore()
    const initial = store.getState()
    const station = initial.selectedStations.selectedStations[0]
    const stations = [station, { ...station, id: '2', station_code: 2, display_label: 'Second station' }]
    const forecast = initial.weatherIndeterminates.forecasts[0]
    const forecasts = stations.map(station => ({
      ...forecast,
      id: rowIDHasher(station.station_code, timestamp),
      station_code: station.station_code,
      station_name: station.display_label
    }))
    store.dispatch(selectedStationsChanged(stations))
    store.dispatch(getWeatherIndeterminatesSuccess({ actuals: [], forecasts, grassCuring: [], predictions: [] }))
    const draft = new MorecastDraftForecast(localStorage)
    const lastEdited = DateTime.now()
    const rows = selectAllMoreCast2Rows(store.getState()).map(row => ({
      ...row,
      tempForecast: { choice: 'MANUAL' as const, value: 40 + row.stationCode }
    }))
    draft.createStoredForecast(rows, lastEdited)
    vi.mocked(fetchWeatherIndeterminates).mockResolvedValue({
      actuals: [{ ...forecasts[0], determinate: WeatherDeterminate.ACTUAL, temperature: 15 }],
      forecasts,
      grassCuring: [],
      predictions: []
    })
    vi.mocked(submitMoreCastForecastRecords).mockClear().mockResolvedValue({
      success: true,
      wf1PublishedCount: 1,
      wf1Skipped: []
    })
    render(
      <Provider store={store}>
        <TabbedDataGrid fromTo={{}} setFromTo={vi.fn()} fetchWeatherIndeterminates={vi.fn()} />
      </Provider>
    )

    await act(async () => {
      await store.dispatch(getWeatherIndeterminates(stations, timestamp.startOf('day'), timestamp.startOf('day')))
    })

    expect(draft.getStoredDraftForecasts()!.rows.map(row => row.stationCode)).toEqual([2])
    expect(draft.getStoredDraftForecasts()!.lastEdited.toMillis()).toBe(lastEdited.toMillis())
    const refreshed = selectAllMoreCast2Rows(store.getState())
    expect(refreshed.find(row => row.stationCode === 1)?.tempActual).toBe(15)
    expect(refreshed.find(row => row.stationCode === 1)?.tempForecast?.value).toBe(20)
    expect(refreshed.find(row => row.stationCode === 2)?.tempForecast?.value).toBe(42)
    expect(screen.getByText(/^Draft saved /)).toBeVisible()

    await userEvent.click(screen.getByTestId('summary-tab-button-unselected'))
    await waitFor(() => expect(screen.getByRole('button', { name: 'Publish to WF1' })).toBeEnabled())
    await userEvent.click(screen.getByRole('button', { name: 'Publish to WF1' }))

    const submitted = vi.mocked(submitMoreCastForecastRecords).mock.calls[0][0]
    expect(submitted.map(row => row.stationCode)).toEqual([2])
    expect(localStorage.getItem(draft.STORAGE_KEY)).toBeNull()
    expect(screen.queryByText(/^Draft saved /)).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Reset' })).toBeDisabled()
  })
})
