import { DateTime } from 'luxon'
import { ModelChoice, StationPrediction } from 'api/moreCast2API'
import { createDateInterval, fillInTheBlanks, parseModelsForStationsHelper } from 'features/moreCast2/util'

const TEST_NUMBER = 7
const TEST_MODEL = ModelChoice.HRDPS
const TEST_DATE = '2023-02-16T20:00:00+00:00'
const TEST_DATE2 = '2023-02-17T20:00:00+00:00'
const TEST_ID = 'test'
const TEST_CODE = 209
const TEST_NAME = 'Victoria'

const createStationPredictionArray = (predictionValue: number | null) => {
  const stationPrediction = {
    bias_adjusted_relative_humidity: predictionValue,
    bias_adjusted_temperature: predictionValue,
    datetime: TEST_DATE,
    precip_24hours: predictionValue,
    id: TEST_ID,
    model: TEST_MODEL,
    relative_humidity: predictionValue,
    station: {
      code: TEST_CODE,
      name: TEST_NAME,
      lat: TEST_NUMBER,
      long: TEST_NUMBER,
      ecodivision_name: null,
      core_season: {
        start_month: TEST_NUMBER,
        start_day: TEST_NUMBER,
        end_month: TEST_NUMBER,
        end_day: TEST_NUMBER
      }
    },
    temperature: predictionValue,
    wind_direction: predictionValue,
    wind_speed: predictionValue
  }
  return [stationPrediction]
}

describe('parseModelsForStationHelper', () => {
  it('should return an empty array when length of stationPredictions array is zero', () => {
    const stationPredictions: StationPrediction[] = []
    const result = parseModelsForStationsHelper(stationPredictions)
    expect(result).toBeDefined()
    expect(result.length).toEqual(0)
  }),
    it('should properly create a Morecast2ForecastRow array from valid station prediction', () => {
      const array = createStationPredictionArray(TEST_NUMBER)
      const result = parseModelsForStationsHelper(array)
      expect(result).toBeDefined()
      expect(result.length).toEqual(1)
      expect(result[0].forDate).toEqual(DateTime.fromISO(TEST_DATE))
      expect(result[0].id).toEqual(TEST_ID)
      expect(result[0].precip.value).toEqual(TEST_NUMBER)
      expect(result[0].precip.choice).toEqual(TEST_MODEL)
      expect(result[0].rh.value).toEqual(TEST_NUMBER)
      expect(result[0].rh.choice).toEqual(TEST_MODEL)
      expect(result[0].temp.value).toEqual(TEST_NUMBER)
      expect(result[0].temp.choice).toEqual(TEST_MODEL)
      expect(result[0].windDirection.value).toEqual(TEST_NUMBER)
      expect(result[0].windDirection.choice).toEqual(TEST_MODEL)
      expect(result[0].windSpeed.value).toEqual(TEST_NUMBER)
      expect(result[0].windSpeed.choice).toEqual(TEST_MODEL)
      expect(result[0].stationCode).toEqual(TEST_CODE)
      expect(result[0].stationName).toEqual(TEST_NAME)
    }),
    it('should set NaN values when numbers are missing in a station prediction', () => {
      const array = createStationPredictionArray(null)
      const result = parseModelsForStationsHelper(array)
      expect(result).toBeDefined()
      expect(result.length).toEqual(1)
      expect(result[0].forDate).toEqual(DateTime.fromISO(TEST_DATE))
      expect(result[0].id).toEqual(TEST_ID)
      expect(result[0].precip.value).toEqual(NaN)
      expect(result[0].rh.value).toEqual(NaN)
      expect(result[0].temp.value).toEqual(NaN)
      expect(result[0].windDirection.value).toEqual(NaN)
      expect(result[0].windSpeed.value).toEqual(NaN)
      expect(result[0].stationCode).toEqual(TEST_CODE)
      expect(result[0].stationName).toEqual(TEST_NAME)
    })
})

describe('fillInTheBlanks', () => {
  const fireCenterStations = [{ code: TEST_CODE, name: TEST_NAME }]
  const stationPredictions = createStationPredictionArray(TEST_NUMBER)
  it('should not create rows when date interval array is empty', () => {
    const dateInterval: string[] = []
    const results = fillInTheBlanks(fireCenterStations, stationPredictions, dateInterval, TEST_MODEL)
    expect(results).toBeDefined()
    expect(results.length).toEqual(stationPredictions.length)
  }),
    it('should not replace existing rows', () => {
      const dateInterval = [TEST_DATE]
      const results = fillInTheBlanks(fireCenterStations, stationPredictions, dateInterval, TEST_MODEL)
      expect(results.length).toEqual(stationPredictions.length)
      expect(results[0]).toEqual(stationPredictions[0])
    }),
    it('should add row for station missing data', () => {
      const dateInterval = [TEST_DATE]
      const stations = [...fireCenterStations, { code: 37, name: 'test' }]
      const results = fillInTheBlanks(stations, stationPredictions, dateInterval, TEST_MODEL)
      expect(results.length).toEqual(stationPredictions.length + 1)
      expect(results.filter(x => x.station.code === 37).length).toEqual(1)
    }),
    it('should add row for each station missing data for one day', () => {
      const dateInterval = [TEST_DATE]
      const stations = [...fireCenterStations, { code: 37, name: 'test' }]
      const results = fillInTheBlanks(stations, stationPredictions, dateInterval, TEST_MODEL)
      expect(results.length).toEqual(stationPredictions.length + 1)
      expect(results.filter(x => x.station.code === 37).length).toEqual(1)
    }),
    it('should add rows for each station missing data for each date interval', () => {
      const dateInterval = [TEST_DATE, TEST_DATE2]
      const results = fillInTheBlanks(fireCenterStations, [], dateInterval, TEST_MODEL)
      expect(results.length).toEqual(dateInterval.length)
      expect(results.filter(x => x.datetime === TEST_DATE).length).toEqual(1)
      expect(results.filter(x => x.datetime === TEST_DATE2).length).toEqual(1)
    }),
    it('should set model type properly in new row', () => {
      const dateInterval = [TEST_DATE]
      const results = fillInTheBlanks(fireCenterStations, [], dateInterval, TEST_MODEL)
      expect(results[0].model).toEqual(TEST_MODEL)
    })
})

describe('createDateInterval', () => {
  it('should return array with single date when fromDate and toDate are the same', () => {
    const result = createDateInterval(DateTime.fromISO(TEST_DATE), DateTime.fromISO(TEST_DATE))
    expect(result).toBeDefined()
    expect(result.length).toEqual(1)
  }),
    it('should return array inclusive of toDate', () => {
      const result = createDateInterval(DateTime.fromISO(TEST_DATE), DateTime.fromISO(TEST_DATE2))
      expect(result).toBeDefined()
      expect(result.length).toEqual(2)
      expect(result[1]).toEqual(TEST_DATE2)
    }),
    it('should return empty array if toDate is before fromDate', () => {
      const result = createDateInterval(DateTime.fromISO(TEST_DATE2), DateTime.fromISO(TEST_DATE))
      expect(result).toBeDefined()
      expect(result.length).toEqual(0)
    })
})
