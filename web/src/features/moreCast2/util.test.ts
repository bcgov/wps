import { DateTime } from 'luxon'
import { ModelChoice, StationPrediction } from 'api/moreCast2API'
import {
  createDateInterval,
  parseForecastsHelper,
  parseModelsForStationsHelper,
  rowIDHasher
} from 'features/moreCast2/util'

const TEST_NUMBER = 7
const TEST_MODEL = ModelChoice.HRDPS
const TEST_DATE = '2023-02-16T20:00:00+00:00'
const TEST_DATE2 = '2023-02-17T20:00:00+00:00'
const TEST_CODE = 209
const TEST_NAME = 'Victoria'

const createStationPredictionArray = (predictionValue: number | null) => {
  const stationPrediction = {
    abbreviation: TEST_MODEL,
    bias_adjusted_relative_humidity: predictionValue,
    bias_adjusted_temperature: predictionValue,
    datetime: TEST_DATE,
    precip_24hours: predictionValue,
    id: rowIDHasher(TEST_CODE, DateTime.fromISO(TEST_DATE)),
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
  })
  it('should properly create a Morecast2ForecastRow array from valid station prediction', () => {
    const array = createStationPredictionArray(TEST_NUMBER)
    const result = parseModelsForStationsHelper(array)
    expect(result).toBeDefined()
    expect(result.length).toEqual(1)
    expect(result[0].forDate).toEqual(DateTime.fromISO(TEST_DATE))
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
  })
  it('should set NaN values when numbers are missing in a station prediction', () => {
    const array = createStationPredictionArray(null)
    const result = parseModelsForStationsHelper(array)
    expect(result).toBeDefined()
    expect(result.length).toEqual(1)
    expect(result[0].forDate).toEqual(DateTime.fromISO(TEST_DATE))
    expect(result[0].precip.value).toEqual(NaN)
    expect(result[0].rh.value).toEqual(NaN)
    expect(result[0].temp.value).toEqual(NaN)
    expect(result[0].windDirection.value).toEqual(NaN)
    expect(result[0].windSpeed.value).toEqual(NaN)
    expect(result[0].stationCode).toEqual(TEST_CODE)
    expect(result[0].stationName).toEqual(TEST_NAME)
  })
})

describe('createDateInterval', () => {
  it('should return array with single date when fromDate and toDate are the same', () => {
    const result = createDateInterval(DateTime.fromISO(TEST_DATE), DateTime.fromISO(TEST_DATE))
    expect(result).toBeDefined()
    expect(result.length).toEqual(1)
  })
  it('should return array inclusive of toDate', () => {
    const result = createDateInterval(DateTime.fromISO(TEST_DATE), DateTime.fromISO(TEST_DATE2))
    expect(result).toBeDefined()
    expect(result.length).toEqual(2)
    expect(result[1]).toEqual(TEST_DATE2)
  })
  it('should return empty array if toDate is before fromDate', () => {
    const result = createDateInterval(DateTime.fromISO(TEST_DATE2), DateTime.fromISO(TEST_DATE))
    expect(result).toBeDefined()
    expect(result.length).toEqual(0)
  })
})

describe('rowIDHasher', () => {
  it('should station code and timestamp as ID', () => {
    const result = rowIDHasher(TEST_CODE, DateTime.fromISO(TEST_DATE))
    expect(result).toEqual(`${TEST_CODE}${DateTime.fromISO(TEST_DATE).toISODate()}`)
  })
})

describe('parseForecastsHelper', () => {
  const buildForecastRecord = (station_code: number) => ({
    station_code,
    for_date: Date.parse('2022-01-01T05:00:00.000Z'),
    precip: 1,
    rh: 1,
    temp: 1,
    wind_direction: 1,
    wind_speed: 1
  })

  const buildStationGroupMember = (
    id: string,
    station_code: number,
    display_label: string,
    fcID: string,
    fzID: string
  ) => ({
    id,
    station_status: 'active',
    station_code,
    display_label,
    fire_centre: {
      id: fcID,
      display_label: 'fc1'
    },
    fire_zone: {
      id: fzID,
      display_label: 'z1',
      fire_centre: 'fc1'
    }
  })

  it('should parse empty set of forecasts/stations', () => {
    const result = parseForecastsHelper([], [])
    expect(result).toEqual([])
  })
  it('should parse empty set of forecasts', () => {
    const result = parseForecastsHelper(
      [],
      [buildStationGroupMember('1', 1, 'one', '1', '1'), buildStationGroupMember('2', 2, 'two', '2', '2')]
    )
    expect(result).toEqual([])
  })
  it('should parse forecasts', () => {
    const result = parseForecastsHelper(
      [buildForecastRecord(1), buildForecastRecord(2)],
      [buildStationGroupMember('1', 1, 'one', '1', '1'), buildStationGroupMember('2', 2, 'two', '2', '2')]
    )
    expect(result).toEqual([
      {
        id: '12021-12-31',
        forDate: DateTime.fromMillis(Date.parse('2022-01-01T05:00:00.000Z')),
        precip: { choice: ModelChoice.FORECAST, value: 1 },
        rh: { choice: ModelChoice.FORECAST, value: 1 },
        stationCode: 1,
        stationName: 'one',
        temp: { choice: ModelChoice.FORECAST, value: 1 },
        windDirection: { choice: ModelChoice.FORECAST, value: 1 },
        windSpeed: { choice: ModelChoice.FORECAST, value: 1 }
      },
      {
        id: '22021-12-31',
        forDate: DateTime.fromMillis(Date.parse('2022-01-01T05:00:00.000Z')),
        precip: { choice: ModelChoice.FORECAST, value: 1 },
        rh: { choice: ModelChoice.FORECAST, value: 1 },
        stationCode: 2,
        stationName: 'two',
        temp: { choice: ModelChoice.FORECAST, value: 1 },
        windDirection: { choice: ModelChoice.FORECAST, value: 1 },
        windSpeed: { choice: ModelChoice.FORECAST, value: 1 }
      }
    ])
  })
  it('should handle case where station is not found in station member list', () => {
    const result = parseForecastsHelper([buildForecastRecord(1)], [])
    expect(result).toEqual([
      {
        id: '12021-12-31',
        forDate: DateTime.fromMillis(Date.parse('2022-01-01T05:00:00.000Z')),
        precip: { choice: ModelChoice.FORECAST, value: 1 },
        rh: { choice: ModelChoice.FORECAST, value: 1 },
        stationCode: 1,
        stationName: '',
        temp: { choice: ModelChoice.FORECAST, value: 1 },
        windDirection: { choice: ModelChoice.FORECAST, value: 1 },
        windSpeed: { choice: ModelChoice.FORECAST, value: 1 }
      }
    ])
  })
  it('should handle case where forecast parameters are missing', () => {
    const result = parseForecastsHelper(
      [{ ...buildForecastRecord(1), precip: NaN, rh: NaN, temp: NaN, wind_speed: NaN, wind_direction: NaN }],
      [buildStationGroupMember('1', 1, 'one', '1', '1')]
    )
    expect(result).toEqual([
      {
        id: '12021-12-31',
        forDate: DateTime.fromMillis(Date.parse('2022-01-01T05:00:00.000Z')),
        precip: { choice: ModelChoice.FORECAST, value: NaN },
        rh: { choice: ModelChoice.FORECAST, value: NaN },
        stationCode: 1,
        stationName: 'one',
        temp: { choice: ModelChoice.FORECAST, value: NaN },
        windDirection: { choice: ModelChoice.FORECAST, value: NaN },
        windSpeed: { choice: ModelChoice.FORECAST, value: NaN }
      }
    ])
  })
})
