import { WeatherDeterminate, type WeatherDeterminateType, type WeatherIndeterminate } from '@wps/api/moreCast2API'
import { DateTime } from 'luxon'
import type { MoreCast2Row } from './interfaces'
import {
  formatElevation,
  getForecastDisplayRows,
  getLatestModelRunTimestamp,
  getModelElevationCellValue,
  getModelElevationData,
  isModelElevationRow
} from './modelElevation'
import { createEmptyMoreCast2Row } from './slices/dataSlice'

const oldRun = '2030-07-04T00:00:00Z'
const latestRun = '2030-07-04T12:00:00Z'

const getModelElevationRow = (
  rows: MoreCast2Row[],
  predictions: WeatherIndeterminate[],
  stations: { station_code: number; elevation: number | null }[],
  stationCode: number
) =>
  getForecastDisplayRows(rows, getModelElevationData(rows, predictions, stations).stationElevations)
    .filter(isModelElevationRow)
    .find(row => row.stationCode === stationCode)

const weatherRow = (stationCode: number, day = 4, timestamps: Partial<MoreCast2Row> = {}): MoreCast2Row => ({
  ...createEmptyMoreCast2Row(
    `station-${stationCode}-${day}`,
    stationCode,
    `Station ${stationCode}`,
    DateTime.utc(2030, 7, day, 20),
    50,
    -120
  ),
  ...timestamps
})

const prediction = (
  stationCode: number,
  model: WeatherDeterminateType,
  run: string | null,
  elevation: number | null
): WeatherIndeterminate => ({
  id: `${stationCode}-${model}-${run}`,
  station_code: stationCode,
  station_name: `Station ${stationCode}`,
  determinate: model,
  utc_timestamp: '2030-07-04T20:00:00Z',
  prediction_run_timestamp: run,
  model_elevation: elevation,
  latitude: 50,
  longitude: -120,
  temperature: null,
  relative_humidity: null,
  precipitation: null,
  wind_direction: null,
  wind_speed: null,
  grass_curing: null,
  fine_fuel_moisture_code: null,
  duff_moisture_code: null,
  drought_code: null,
  initial_spread_index: null,
  build_up_index: null,
  fire_weather_index: null,
  danger_rating: null
})

describe('latest model run timestamp', () => {
  it('uses the latest valid instant across stations and forecast dates', () => {
    const rows = [
      weatherRow(1, 4, { predictionRunTimestampHRDPS: oldRun }),
      weatherRow(2, 5, { predictionRunTimestampHRDPS: latestRun }),
      weatherRow(3, 6, { predictionRunTimestampHRDPS: 'invalid' })
    ]
    expect(getLatestModelRunTimestamp(rows, WeatherDeterminate.HRDPS)?.toMillis()).toBe(
      DateTime.fromISO(latestRun).toMillis()
    )
    expect(getLatestModelRunTimestamp(rows, WeatherDeterminate.ECMWF)).toBeNull()
    expect(getLatestModelRunTimestamp(undefined, WeatherDeterminate.HRDPS)).toBeNull()
  })
})

describe('model elevation rows', () => {
  it('adds one header per station without changing the weather rows or their order', () => {
    const rows = [weatherRow(1), weatherRow(1, 5), weatherRow(2)]
    const originalRows = [...rows]
    const stations = [{ station_code: 1, elevation: 900 }]
    const displayRows = getForecastDisplayRows(rows, getModelElevationData(rows, [], stations).stationElevations)
    expect(displayRows.map(row => row.id)).toEqual([
      'model-elevation-1',
      rows[0].id,
      rows[1].id,
      'model-elevation-2',
      rows[2].id
    ])
    expect(displayRows.filter(row => !isModelElevationRow(row))).toEqual(rows)
    expect(getModelElevationRow(rows, [], stations, 1)).toMatchObject({
      id: 'model-elevation-1',
      stationCode: 1,
      stationName: 'Station 1',
      stationElevation: 900
    })
    expect(getModelElevationRow(rows, [], stations, 2)).toMatchObject({
      id: 'model-elevation-2',
      stationCode: 2,
      stationElevation: null
    })
    expect(rows).toEqual(originalRows)
    expect(getForecastDisplayRows([], getModelElevationData([], [], stations).stationElevations)).toEqual([])
    expect(getModelElevationRow(rows, [], stations, 3)).toBeUndefined()
  })

  it('matches each model header run, normalizes UTC, and excludes hidden stations and bias data', () => {
    const rows = [
      weatherRow(1, 4, { predictionRunTimestampHRDPS: oldRun, predictionRunTimestampECMWF: oldRun }),
      weatherRow(1, 5, { predictionRunTimestampHRDPS: latestRun, predictionRunTimestampECMWF: oldRun }),
      weatherRow(2, 4, { predictionRunTimestampHRDPS: oldRun })
    ]
    const forecasts = [
      prediction(1, 'HRDPS', oldRun, 800),
      prediction(1, 'HRDPS', '2030-07-04T12:00:00+00:00', 850.4),
      prediction(1, 'ECMWF', '2030-07-03T17:00:00-07:00', 1100),
      prediction(1, 'HRDPS_BIAS', latestRun, 999),
      prediction(2, 'HRDPS', oldRun, 700),
      prediction(3, 'HRDPS', '2030-07-05T00:00:00Z', 500)
    ]
    const row = getModelElevationRow(rows, forecasts, [{ station_code: 1, elevation: 900 }], 1)!
    const otherStation = getModelElevationRow(rows, forecasts, [], 2)!
    expect(row.modelElevations).toMatchObject({ HRDPS: 850.4, ECMWF: 1100 })
    expect(row.modelElevations.HRDPS_BIAS).toBeUndefined()
    expect(getModelElevationCellValue(otherStation, 'tempHRDPS', 'HRDPS')).toBe('N/A')
    expect(getModelElevationCellValue(row, 'tempHRDPS_BIAS', 'HRDPS_BIAS')).toBe('')
    expect(getModelElevationCellValue(row, 'tempForecast', 'Forecast')).toBe('')
    expect(getModelElevationCellValue(row, 'tempActual', 'Actual')).toBe('')
    expect(getModelElevationCellValue(row, 'grassCuringCWFIS', 'CWFIS')).toBe('')
    expect(getModelElevationCellValue(row, 'tempHRDPS', 'HRDPS')).toBe('850 m')
    expect(getModelElevationCellValue(row, 'rhHRDPS', 'HRDPS')).toBe('850 m')
    expect(getModelElevationCellValue(row, 'forDate')).toBe('')
  })

  it.each([850.4, 0, null, undefined])(
    'keeps the first matching height of %s across repeated predictions',
    elevation => {
      const rows = [weatherRow(1, 4, { predictionRunTimestampHRDPS: latestRun })]
      const first = { ...prediction(1, 'HRDPS', latestRun, null), model_elevation: elevation }
      const forecasts = [prediction(1, 'HRDPS', oldRun, 800), first, prediction(1, 'HRDPS', latestRun, 950)]
      const data = getModelElevationData(rows, forecasts, [])
      expect(data.stationElevations.get(1)?.modelElevations.HRDPS).toBe(elevation ?? null)
    }
  )

  it('keeps station metadata and null model heights while forecast rows are unavailable', () => {
    const data = getModelElevationData([], [], [{ station_code: 1, elevation: 900 }])
    expect(data.stationElevations.get(1)).toMatchObject({
      stationElevation: 900,
      modelElevations: { HRDPS: null, ECMWF: null }
    })
  })

  it.each([null, undefined])('keeps a latest height of %s unavailable instead of using an older height', elevation => {
    const rows = [weatherRow(1, 4, { predictionRunTimestampHRDPS: latestRun })]
    const latest = { ...prediction(1, 'HRDPS', latestRun, null), model_elevation: elevation }
    const row = getModelElevationRow(rows, [prediction(1, 'HRDPS', oldRun, 800), latest], [], 1)!
    expect(getModelElevationCellValue(row, 'tempHRDPS', 'HRDPS')).toBe('N/A')
  })

  it('recomputes the selected run when the displayed station or date data changes', () => {
    const forecasts = [prediction(1, 'HRDPS', oldRun, 800), prediction(2, 'HRDPS', latestRun, 900)]
    const older = weatherRow(1, 4, { predictionRunTimestampHRDPS: oldRun })
    const newer = weatherRow(2, 5, { predictionRunTimestampHRDPS: latestRun })
    expect(getModelElevationRow([older, newer], forecasts, [], 1)?.modelElevations.HRDPS).toBeNull()
    expect(getModelElevationRow([older, newer], forecasts, [], 2)?.modelElevations.HRDPS).toBe(900)
    expect(getModelElevationRow([older], forecasts, [], 1)?.modelElevations.HRDPS).toBe(800)
  })
})

it.each<[number | null, string]>([
  [0, '0 m'],
  [-5.6, '-6 m'],
  [1234.57, '1,235 m'],
  [null, 'N/A'],
  [Number.NaN, 'N/A']
])('formats elevation %s as %s', (elevation, expected) => expect(formatElevation(elevation)).toBe(expected))
