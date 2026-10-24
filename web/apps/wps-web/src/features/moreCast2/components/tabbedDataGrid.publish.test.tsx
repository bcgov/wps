import { configureStore } from '@reduxjs/toolkit'
import { render, screen, waitFor } from '@testing-library/react'
import { userEvent } from '@testing-library/user-event'
import { submitMoreCastForecastRecords, WeatherDeterminate } from '@wps/api/moreCast2API'
import rootReducer from 'app/rootReducer'
import { ROLES } from 'features/auth/roles'
import { MorecastDraftForecast } from 'features/moreCast2/forecastDraft'
import { selectAllMoreCast2Rows } from 'features/moreCast2/slices/dataSlice'
import { DateTime } from 'luxon'
import { Provider } from 'react-redux'
import { vi } from 'vitest'
import TabbedDataGrid from './TabbedDataGrid'

vi.mock('@wps/api/moreCast2API', async importOriginal => ({
  ...(await importOriginal<typeof import('@wps/api/moreCast2API')>()),
  submitMoreCastForecastRecords: vi.fn()
}))

const timestamp = DateTime.utc(2030, 7, 4, 20)
const skipped = [{ station_code: 1, station_name: 'Test station', for_date: timestamp.toMillis() }]

const renderPublishing = async (refresh = vi.fn()) => {
  localStorage.clear()
  const initial = rootReducer(undefined, { type: 'test' })
  const testStore = configureStore({
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
})
