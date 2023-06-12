import {
  WeatherDeterminate,
  WeatherDeterminateChoices,
  WeatherIndeterminate,
  WeatherIndeterminatePayload
} from 'api/moreCast2API'
import dataSliceReducer, {
  createMoreCast2Rows,
  fillMissingPredictions,
  fillMissingWeatherIndeterminates,
  initialState,
  getWeatherIndeterminatesFailed,
  getWeatherIndeterminatesStart,
  getWeatherIndeterminatesSuccess
} from 'features/moreCast2/slices/dataSlice'
import { DateTime } from 'luxon'

const FROM_DATE_STRING = '2023-04-27T20:00:00+00:00'
const TO_DATE_STRING = '2023-04-28T20:00:00+00:00'
const FROM_DATE_TIME = DateTime.fromISO(FROM_DATE_STRING)
const TO_DATE_TIME = DateTime.fromISO(TO_DATE_STRING)
const PRECIP = 1
const RH = 75
const TEMP = 10
const WIND_DIRECTION = 180
const WIND_SPEED = 5

const modelDeterminates = WeatherDeterminateChoices.filter(
  determinate =>
    determinate !== WeatherDeterminate.ACTUAL &&
    determinate !== WeatherDeterminate.FORECAST &&
    determinate !== WeatherDeterminate.NULL
)

const weatherIndeterminateGenerator = (
  station_code: number,
  station_name: string,
  determinate: WeatherDeterminate,
  utc_timestamp: string,
  precipValue?: number
) => {
  return {
    id: `${station_code}${utc_timestamp}`,
    station_code,
    station_name,
    determinate,
    utc_timestamp,
    precipitation: precipValue ?? PRECIP,
    relative_humidity: RH,
    temperature: TEMP,
    wind_direction: WIND_DIRECTION,
    wind_speed: WIND_SPEED
  }
}

const predictionGenerator = (station_code: number, station_name: string, date: string) => {
  const predictions: WeatherIndeterminate[] = []
  for (const model of modelDeterminates) {
    const prediction = weatherIndeterminateGenerator(station_code, station_name, model, date)
    predictions.push(prediction)
  }
  return predictions
}

describe('dataSlice', () => {
  describe('reducer', () => {
    const dummyError = 'an error'
    it('should be initialized with correct state flags', () => {
      expect(dataSliceReducer(undefined, { type: undefined })).toEqual(initialState)
    })
    it('should set loading = true when getWeatherIndeterminatesStart is called', () => {
      expect(dataSliceReducer(initialState, getWeatherIndeterminatesStart())).toEqual({
        ...initialState,
        loading: true
      })
    })
    it('should set loading = false when getWeatherIndeterminatesSuccess is called', () => {
      expect(
        dataSliceReducer(initialState, getWeatherIndeterminatesSuccess({ actuals: [], forecasts: [], predictions: [] }))
      ).toEqual({
        ...initialState,
        loading: false
      })
    })
    it('should set weather indeterminates when getWeatherIndeterminatesSuccess is called', () => {
      const actuals: WeatherIndeterminate[] = [
        {
          id: 'test1',
          station_code: 1,
          station_name: 'station',
          determinate: WeatherDeterminate.ACTUAL,
          utc_timestamp: '2023-04-21',
          precipitation: 0.5,
          relative_humidity: 55,
          temperature: 12,
          wind_direction: 180,
          wind_speed: 5.3
        }
      ]
      const forecasts: [] = []
      const predictions: WeatherIndeterminate[] = [
        {
          id: 'test3',
          station_code: 3,
          station_name: 'prediction station',
          determinate: WeatherDeterminate.GDPS,
          utc_timestamp: '2023-04-22',
          precipitation: 1.5,
          relative_humidity: 75,
          temperature: 5,
          wind_direction: 65,
          wind_speed: 10.7
        }
      ]
      const payload: WeatherIndeterminatePayload = {
        actuals,
        forecasts,
        predictions
      }
      expect(dataSliceReducer(initialState, getWeatherIndeterminatesSuccess(payload))).toEqual({
        ...initialState,
        actuals: payload.actuals,
        forecasts: payload.forecasts,
        predictions: payload.predictions
      })
    })
    it('should set a value for error state when getWeatherIndeterminatesFailed is called', () => {
      expect(dataSliceReducer(initialState, getWeatherIndeterminatesFailed(dummyError)).error).not.toBeNull()
    })
  })
  describe('fillMissingWeatherIndeterminates', () => {
    const fromDate = DateTime.fromISO('2023-04-27T20:00:00+00:00')
    const toDate = DateTime.fromISO('2023-04-28T20:00:00+00:00')
    it('should populate a missing actual per station per day when no weather indeterminates exist', () => {
      const items: WeatherIndeterminate[] = []
      const stationMap = new Map<number, string>()
      stationMap.set(1, 'test')
      const result = fillMissingWeatherIndeterminates(items, fromDate, toDate, stationMap, WeatherDeterminate.ACTUAL)
      expect(result.length).toBe(2)
    })
    it('should populate missing actuals per station per day when a weather indeterminate already exists', () => {
      const weatherIndeterminate = weatherIndeterminateGenerator(1, 'test', WeatherDeterminate.ACTUAL, FROM_DATE_STRING)
      const items: WeatherIndeterminate[] = [weatherIndeterminate]
      const stationMap = new Map<number, string>()
      stationMap.set(1, 'test')
      const result = fillMissingWeatherIndeterminates(
        items,
        FROM_DATE_TIME,
        TO_DATE_TIME,
        stationMap,
        WeatherDeterminate.ACTUAL
      )
      expect(result.length).toBe(2)
      expect(result[0]).toEqual(weatherIndeterminate)
    })
    it('should not add actuals if expected actuals already exist', () => {
      const weatherIndeterminate = weatherIndeterminateGenerator(1, 'test', WeatherDeterminate.ACTUAL, FROM_DATE_STRING)
      const weatherIndeterminate2 = weatherIndeterminateGenerator(1, 'test', WeatherDeterminate.ACTUAL, TO_DATE_STRING)
      const items: WeatherIndeterminate[] = [weatherIndeterminate, weatherIndeterminate2]
      const stationMap = new Map<number, string>()
      stationMap.set(1, 'test')
      const result = fillMissingWeatherIndeterminates(
        items,
        FROM_DATE_TIME,
        TO_DATE_TIME,
        stationMap,
        WeatherDeterminate.ACTUAL
      )
      expect(result.length).toBe(2)
      expect(result[0]).toEqual(weatherIndeterminate)
      expect(result[1]).toEqual(weatherIndeterminate2)
    })
  })
  describe('fillMissingPredictions', () => {
    const fromDate = DateTime.fromISO('2023-04-27T20:00:00+00:00')
    const toDate = DateTime.fromISO('2023-04-28T20:00:00+00:00')
    it('should populate a missing prediction per station per day per weather model when no predictions exist', () => {
      const items: WeatherIndeterminate[] = []
      const stationMap = new Map<number, string>()
      stationMap.set(1, 'test')
      const result = fillMissingPredictions(items, fromDate, toDate, stationMap)
      // Expect 2 predictions per weather model
      expect(result.length).toBe(2 * modelDeterminates.length)
    })
    it('should populate missing predictions per station per day per weather model when a prediction already exists', () => {
      const weatherPrediction = weatherIndeterminateGenerator(1, 'test', WeatherDeterminate.HRDPS, FROM_DATE_STRING)
      const items: WeatherIndeterminate[] = [weatherPrediction]
      const stationMap = new Map<number, string>()
      stationMap.set(1, 'test')
      const result = fillMissingPredictions(items, FROM_DATE_TIME, TO_DATE_TIME, stationMap)
      // Expect 2 predictions per weather model
      expect(result.length).toBe(2 * modelDeterminates.length)
      expect(result[0]).toEqual(weatherPrediction)
    })
    it('should not add predictions if expected predictions already exist', () => {
      const weatherIndeterminates = predictionGenerator(1, 'test', FROM_DATE_STRING)
      const stationMap = new Map<number, string>()
      stationMap.set(1, 'test')
      const result = fillMissingPredictions(weatherIndeterminates, FROM_DATE_TIME, FROM_DATE_TIME, stationMap)
      expect(result.length).toBe(weatherIndeterminates.length)
    })
  })
  describe('createMoreCast2Rows', () => {
    it('should create one row per station per date', () => {
      const stationCode = 1
      const stationName = 'test'
      const actuals = [
        weatherIndeterminateGenerator(stationCode, stationName, WeatherDeterminate.ACTUAL, FROM_DATE_STRING)
      ]
      const forecasts = [
        weatherIndeterminateGenerator(stationCode, stationName, WeatherDeterminate.NULL, FROM_DATE_STRING)
      ]
      const predictions = predictionGenerator(stationCode, stationName, FROM_DATE_STRING)
      const rows = createMoreCast2Rows(actuals, forecasts, predictions)
      expect(rows.length).toBe(1)
      const row = rows[0]
      expect(row.stationCode).toBe(stationCode)
      expect(row.stationName).toBe(stationName)
      expect(row.precipActual).toBe(PRECIP)
      expect(row.rhActual).toBe(RH)
      expect(row.tempActual).toBe(TEMP)
      expect(row.windDirectionActual).toBe(WIND_DIRECTION)
      expect(row.windSpeedActual).toBe(WIND_SPEED)
    })
    it('should set precip to 0 when row has no precipActual', () => {
      const stationCode = 1
      const stationName = 'test'
      const actuals = [
        weatherIndeterminateGenerator(stationCode, stationName, WeatherDeterminate.ACTUAL, FROM_DATE_STRING, NaN)
      ]
      const forecasts = [
        weatherIndeterminateGenerator(stationCode, stationName, WeatherDeterminate.NULL, FROM_DATE_STRING, NaN)
      ]
      const predictions = predictionGenerator(stationCode, stationName, FROM_DATE_STRING)
      const rows = createMoreCast2Rows(actuals, forecasts, predictions)
      const row = rows[0]
      expect(row.precipForecast?.choice).toBe(WeatherDeterminate.NULL)
      expect(row.precipForecast?.value).toBe(0)
    })
    it('should not set precip to 0 when row has a value for precipActual', () => {
      const stationCode = 1
      const stationName = 'test'
      const actuals = [
        weatherIndeterminateGenerator(stationCode, stationName, WeatherDeterminate.ACTUAL, FROM_DATE_STRING, 1)
      ]
      const forecasts = [
        weatherIndeterminateGenerator(stationCode, stationName, WeatherDeterminate.NULL, FROM_DATE_STRING, NaN)
      ]
      const predictions = predictionGenerator(stationCode, stationName, FROM_DATE_STRING)
      const rows = createMoreCast2Rows(actuals, forecasts, predictions)
      const row = rows[0]
      expect(row.precipForecast?.choice).toBe(WeatherDeterminate.NULL)
      expect(row.precipForecast?.value).toBe(NaN)
    })
    it('should not overwrite forecasted precip value', () => {
      const stationCode = 1
      const stationName = 'test'
      const actuals = [
        weatherIndeterminateGenerator(stationCode, stationName, WeatherDeterminate.ACTUAL, FROM_DATE_STRING, 1)
      ]
      const forecasts = [
        weatherIndeterminateGenerator(stationCode, stationName, WeatherDeterminate.NULL, FROM_DATE_STRING, 1)
      ]
      const predictions = predictionGenerator(stationCode, stationName, FROM_DATE_STRING)
      const rows = createMoreCast2Rows(actuals, forecasts, predictions)
      const row = rows[0]
      expect(row.precipForecast?.choice).toBe(WeatherDeterminate.NULL)
      expect(row.precipForecast?.value).toBe(1)
    })
  })
})
