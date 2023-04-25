import { DateTime } from 'luxon'
import { ModelChoice, StationPrediction } from 'api/moreCast2API'
import {
  createDateInterval,
  parseModelsForStationsHelper,
  rowIDHasher,
  buildListOfRowsToDisplay,
  marshalAllMoreCast2ForecastRowsByStationAndDate
} from 'features/moreCast2/util'
import { MoreCast2ForecastRow } from 'features/moreCast2/interfaces'

const TEST_NUMBER = 7
const TEST_MODEL = ModelChoice.HRDPS
const TEST_DATE = '2023-02-16T20:00:00+00:00'
const TEST_DATE2 = '2023-02-17T20:00:00+00:00'
const TEST_DATE3 = '2023-02-18T20:00:00+00:00'
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

const generateRowsForTwoStations = (): MoreCast2ForecastRow[] => [
  {
    id: rowIDHasher(1, DateTime.fromISO(TEST_DATE)),
    stationCode: 1,
    stationName: 'one',
    forDate: DateTime.fromISO(TEST_DATE),
    temp: { value: 1, choice: ModelChoice.GDPS },
    rh: { value: 1, choice: ModelChoice.GDPS },
    precip: { value: 1, choice: ModelChoice.GDPS },
    windSpeed: { value: 1, choice: ModelChoice.GDPS },
    windDirection: { value: 1, choice: ModelChoice.GDPS }
  },
  {
    id: rowIDHasher(2, DateTime.fromISO(TEST_DATE2)),
    stationCode: 2,
    stationName: 'two',
    forDate: DateTime.fromISO(TEST_DATE2),
    temp: { value: 1, choice: ModelChoice.GDPS },
    rh: { value: 1, choice: ModelChoice.GDPS },
    precip: { value: 1, choice: ModelChoice.GDPS },
    windSpeed: { value: 1, choice: ModelChoice.GDPS },
    windDirection: { value: 1, choice: ModelChoice.GDPS }
  }
]

const generateRowsForStation = (stationCode: number, stationName: string): MoreCast2ForecastRow[] => [
  {
    id: rowIDHasher(stationCode, DateTime.fromISO(TEST_DATE)),
    stationCode: stationCode,
    stationName: stationName,
    forDate: DateTime.fromISO(TEST_DATE),
    temp: { value: 1, choice: ModelChoice.GDPS },
    rh: { value: 1, choice: ModelChoice.GDPS },
    precip: { value: 1, choice: ModelChoice.GDPS },
    windSpeed: { value: 1, choice: ModelChoice.GDPS },
    windDirection: { value: 1, choice: ModelChoice.GDPS }
  },
  {
    id: rowIDHasher(stationCode, DateTime.fromISO(TEST_DATE2)),
    stationCode: stationCode,
    stationName: stationName,
    forDate: DateTime.fromISO(TEST_DATE2),
    temp: { value: 1, choice: ModelChoice.GDPS },
    rh: { value: 1, choice: ModelChoice.GDPS },
    precip: { value: 1, choice: ModelChoice.GDPS },
    windSpeed: { value: 1, choice: ModelChoice.GDPS },
    windDirection: { value: 1, choice: ModelChoice.GDPS }
  },
  {
    id: rowIDHasher(stationCode, DateTime.fromISO(TEST_DATE3)),
    stationCode: stationCode,
    stationName: stationName,
    forDate: DateTime.fromISO(TEST_DATE3),
    temp: { value: 5, choice: ModelChoice.GDPS },
    rh: { value: 10, choice: ModelChoice.GDPS },
    precip: { value: 1, choice: ModelChoice.GDPS },
    windSpeed: { value: 1, choice: ModelChoice.GDPS },
    windDirection: { value: 1, choice: ModelChoice.GDPS }
  }
]

const generateRowsWithActuals = (stationCode: number, stationName: string): MoreCast2ForecastRow[] => [
  {
    id: rowIDHasher(stationCode, DateTime.fromISO(TEST_DATE)),
    stationCode: stationCode,
    stationName: stationName,
    forDate: DateTime.fromISO(TEST_DATE),
    temp: { value: 1, choice: ModelChoice.ACTUAL },
    rh: { value: 1, choice: ModelChoice.ACTUAL },
    precip: { value: 1, choice: ModelChoice.ACTUAL },
    windSpeed: { value: 1, choice: ModelChoice.ACTUAL },
    windDirection: { value: 1, choice: ModelChoice.ACTUAL }
  },
  {
    id: rowIDHasher(stationCode, DateTime.fromISO(TEST_DATE2)),
    stationCode: stationCode,
    stationName: stationName,
    forDate: DateTime.fromISO(TEST_DATE2),
    temp: { value: 1, choice: ModelChoice.ACTUAL },
    rh: { value: 1, choice: ModelChoice.ACTUAL },
    precip: { value: 1, choice: ModelChoice.ACTUAL },
    windSpeed: { value: 1, choice: ModelChoice.ACTUAL },
    windDirection: { value: 1, choice: ModelChoice.ACTUAL }
  }
]

const generateStationGroupMember = (code: number, name: string) => ({
  id: '1',
  fire_centre: { id: '1', display_label: 'test' },
  fire_zone: { id: '1', display_label: 'test', fire_centre: 'test' },
  station_status: 'ACTIVE',
  station_code: code,
  display_label: name
})

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
