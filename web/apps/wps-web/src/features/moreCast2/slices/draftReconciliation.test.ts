import { configureStore } from '@reduxjs/toolkit'
import { fetchWeatherIndeterminates, WeatherDeterminate, type WeatherIndeterminate } from '@wps/api/moreCast2API'
import type { StationGroupMember } from '@wps/api/stationAPI'
import rootReducer from 'app/rootReducer'
import { MorecastDraftForecast } from 'features/moreCast2/forecastDraft'
import { rowIDHasher } from 'features/moreCast2/util'
import { DateTime } from 'luxon'
import { vi } from 'vitest'
import { createEmptyMoreCast2Row, getWeatherIndeterminates, selectAllMoreCast2Rows } from './dataSlice'

vi.mock('@wps/api/moreCast2API', async importOriginal => ({
  ...(await importOriginal<typeof import('@wps/api/moreCast2API')>()),
  fetchWeatherIndeterminates: vi.fn()
}))

const timestamp = DateTime.utc(2030, 7, 4, 20)
const stations: StationGroupMember[] = [1, 2].map(code => ({
  id: String(code),
  display_label: `Station ${code}`,
  station_code: code,
  station_status: 'ACTIVE',
  fire_centre: { id: '1', display_label: 'Centre' },
  fire_zone: { id: '1', display_label: 'Zone', fire_centre: '1' }
}))

const reading = (code: number, temperature: number | null): WeatherIndeterminate => ({
  id: rowIDHasher(code, timestamp),
  station_code: code,
  station_name: `Station ${code}`,
  utc_timestamp: timestamp.toISO()!,
  determinate: WeatherDeterminate.ACTUAL,
  latitude: 50,
  longitude: -120,
  temperature,
  relative_humidity: null,
  precipitation: null,
  wind_speed: null,
  wind_direction: null,
  grass_curing: null,
  fine_fuel_moisture_code: null,
  duff_moisture_code: null,
  drought_code: null,
  initial_spread_index: null,
  build_up_index: null,
  fire_weather_index: null,
  danger_rating: null,
  prediction_run_timestamp: null
})

const seedDraft = (code: number, date = timestamp) => {
  const row = createEmptyMoreCast2Row(rowIDHasher(code, date), code, `Station ${code}`, date, 50, -120)
  row.tempForecast = { choice: 'MANUAL', value: 42 }
  return row
}

describe('reconciling drafts after weather fetches', () => {
  const draft = new MorecastDraftForecast(localStorage)
  const lastEdited = timestamp.minus({ hours: 1 })

  beforeEach(() => localStorage.clear())
  afterEach(() => {
    localStorage.clear()
    vi.restoreAllMocks()
  })

  test.each([0, null])(
    'removes a returned actual with temperature %s before rebuilding the grid',
    async temperature => {
      const rows = [seedDraft(1), seedDraft(2), seedDraft(3, timestamp.plus({ days: 1 }))]
      localStorage.setItem(draft.STORAGE_KEY, JSON.stringify({ rows, lastEdited }))
      vi.mocked(fetchWeatherIndeterminates).mockResolvedValue({
        actuals: [reading(1, temperature)],
        forecasts: [],
        grassCuring: [],
        predictions: []
      })
      const store = configureStore({ reducer: rootReducer })

      await store.dispatch(getWeatherIndeterminates(stations, timestamp.startOf('day'), timestamp.startOf('day')))

      expect(draft.getStoredDraftForecasts()!.rows.map(row => row.stationCode)).toEqual([2, 3])
      expect(draft.getStoredDraftForecasts()!.lastEdited.toISO()).toBe(lastEdited.toISO())
      const gridRows = selectAllMoreCast2Rows(store.getState())
      expect(gridRows.find(row => row.stationCode === 1)?.tempForecast?.value).not.toBe(42)
      expect(gridRows.find(row => row.stationCode === 2)?.tempForecast?.value).toBe(42)
    }
  )

  test('keeps drafts when actuals are only generated placeholders', async () => {
    const rows = [seedDraft(1), seedDraft(2)]
    localStorage.setItem(draft.STORAGE_KEY, JSON.stringify({ rows, lastEdited }))
    vi.mocked(fetchWeatherIndeterminates).mockResolvedValue({
      actuals: [],
      forecasts: [],
      grassCuring: [],
      predictions: []
    })
    const store = configureStore({ reducer: rootReducer })

    await store.dispatch(getWeatherIndeterminates(stations, timestamp.startOf('day'), timestamp.startOf('day')))

    expect(store.getState().weatherIndeterminates.actuals).toHaveLength(2)
    expect(draft.getStoredDraftForecasts()!.rows.map(row => row.id)).toEqual(rows.map(row => row.id))
  })

  test('leaves the entire stored draft unchanged when the fetch fails', async () => {
    const rows = [seedDraft(1), seedDraft(3, DateTime.utc(2000, 1, 1))]
    const original = JSON.stringify({ rows, lastEdited })
    localStorage.setItem(draft.STORAGE_KEY, original)
    vi.mocked(fetchWeatherIndeterminates).mockRejectedValue(new Error('WF1 unavailable'))
    const store = configureStore({ reducer: rootReducer })

    await store.dispatch(getWeatherIndeterminates(stations, timestamp.startOf('day'), timestamp.startOf('day')))

    expect(store.getState().weatherIndeterminates.error).toContain('WF1 unavailable')
    expect(localStorage.getItem(draft.STORAGE_KEY)).toBe(original)
  })
})
