import { DateTime } from 'luxon'
import { ModelChoice, StationPrediction } from 'api/moreCast2API'
import {
  createDateInterval,
  filterRowsByModelType,
  fillInTheModelBlanks,
  parseModelsForStationsHelper,
  replaceColumnValuesFromPrediction,
  rowIDHasher
} from 'features/moreCast2/util'
import { MoreCast2ForecastRow } from 'features/moreCast2/interfaces'
import { ColPrediction } from 'features/moreCast2/slices/columnModelSlice'
import { StationGroupMember } from 'api/stationAPI'

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

export const generateExistingRows = (): MoreCast2ForecastRow[] => [
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

describe('fillInTheBlanks', () => {
  const fireCenterStations: StationGroupMember[] = [
    {
      id: '1',
      fire_centre: { id: '1', display_label: 'test' },
      fire_zone: { id: '1', display_label: 'test', fire_centre: 'test' },
      station_status: 'ACTIVE',
      station_code: TEST_CODE,
      display_label: TEST_NAME
    }
  ]
  const stationPredictions: StationPrediction[] = createStationPredictionArray(TEST_NUMBER)
  it('should not create rows when date interval array is empty', () => {
    const dateInterval: string[] = []
    const results = fillInTheModelBlanks(fireCenterStations, stationPredictions, dateInterval, TEST_MODEL)
    expect(results).toBeDefined()
    expect(results.length).toEqual(stationPredictions.length)
  })
  it('should not replace existing rows', () => {
    const dateInterval = [TEST_DATE]
    const results = fillInTheModelBlanks(fireCenterStations, stationPredictions, dateInterval, TEST_MODEL)
    expect(results.length).toEqual(stationPredictions.length)
    expect(results[0]).toEqual(stationPredictions[0])
  })
  it('should add row for station missing data', () => {
    const dateInterval = [TEST_DATE]
    const stations = [...fireCenterStations, generateStationGroupMember(37, 'test')]
    const results = fillInTheModelBlanks(stations, stationPredictions, dateInterval, TEST_MODEL)
    expect(results.length).toEqual(stationPredictions.length + 1)
    expect(results.filter(x => x.station.code === 37).length).toEqual(1)
  })
  it('should add row for each station missing data for one day', () => {
    const dateInterval = [TEST_DATE]
    const stations = [...fireCenterStations, generateStationGroupMember(37, 'test')]
    const results = fillInTheModelBlanks(stations, stationPredictions, dateInterval, TEST_MODEL)
    expect(results.length).toEqual(stationPredictions.length + 1)
    expect(results.filter(x => x.station.code === 37).length).toEqual(1)
  })
  it('should add rows for each station missing data for each date interval', () => {
    const dateInterval = [TEST_DATE, TEST_DATE2]
    const results = fillInTheModelBlanks(fireCenterStations, [], dateInterval, TEST_MODEL)
    expect(results.length).toEqual(dateInterval.length)
    expect(results.filter(x => x.datetime === TEST_DATE).length).toEqual(1)
    expect(results.filter(x => x.datetime === TEST_DATE2).length).toEqual(1)
  })
  it('should set model type properly in new row', () => {
    const dateInterval = [TEST_DATE]
    const results = fillInTheModelBlanks(fireCenterStations, [], dateInterval, TEST_MODEL)
    expect(results[0].abbreviation).toEqual(TEST_MODEL)
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

describe('replaceColumnValuesFromPrediction', () => {
  it('should replace the correct row', () => {
    const existingRows: MoreCast2ForecastRow[] = generateExistingRows()

    const colPrediction: ColPrediction = {
      colField: 'temp',
      modelType: 'HRDPS',
      stationPredictions: [
        {
          abbreviation: ModelChoice.HRDPS,
          bias_adjusted_relative_humidity: null,
          bias_adjusted_temperature: null,
          datetime: TEST_DATE,
          precip_24hours: 2,
          id: '1',
          relative_humidity: 2,
          station: {
            code: 1,
            name: 'one',
            lat: 1,
            long: 1,
            ecodivision_name: null,
            core_season: {
              start_month: 1,
              start_day: 1,
              end_month: 1,
              end_day: 1
            }
          },
          temperature: 2,
          wind_direction: 2,
          wind_speed: 2
        },
        {
          abbreviation: ModelChoice.HRDPS,
          bias_adjusted_relative_humidity: null,
          bias_adjusted_temperature: null,
          datetime: TEST_DATE2,
          precip_24hours: 2,
          id: '2',
          relative_humidity: 2,
          station: {
            code: 2,
            name: 'two',
            lat: 1,
            long: 1,
            ecodivision_name: null,
            core_season: {
              start_month: 1,
              start_day: 1,
              end_month: 1,
              end_day: 1
            }
          },
          temperature: 2,
          wind_direction: 2,
          wind_speed: 2
        }
      ]
    }
    const result = replaceColumnValuesFromPrediction(
      existingRows,
      [generateStationGroupMember(1, 'one'), generateStationGroupMember(2, 'two')],
      [TEST_DATE, TEST_DATE2],
      colPrediction
    )
    expect(result).toHaveLength(2)
    expect(result[0].id).toEqual(existingRows[0].id)
    expect(result[0].stationCode).toEqual(existingRows[0].stationCode)
    expect(result[0].stationName).toEqual(existingRows[0].stationName)
    expect(result[0].forDate).toEqual(DateTime.fromISO(TEST_DATE))
    expect(result[0].temp).toEqual({ value: 2, choice: ModelChoice.HRDPS })

    // Other rows remain unchanged
    expect(result[0].rh).toEqual(existingRows[0].rh)
    expect(result[0].precip).toEqual(existingRows[0].precip)
    expect(result[0].windSpeed).toEqual(existingRows[0].windSpeed)
    expect(result[0].windDirection).toEqual(existingRows[0].windDirection)

    expect(result[1].id).toEqual(existingRows[1].id)
    expect(result[1].stationCode).toEqual(existingRows[1].stationCode)
    expect(result[1].stationName).toEqual(existingRows[1].stationName)
    expect(result[1].forDate).toEqual(DateTime.fromISO(TEST_DATE2))
    expect(result[1].temp).toEqual({ value: 2, choice: ModelChoice.HRDPS })

    // Other rows remain unchanged
    expect(result[1].rh).toEqual(existingRows[1].rh)
    expect(result[1].precip).toEqual(existingRows[1].precip)
    expect(result[1].windSpeed).toEqual(existingRows[1].windSpeed)
    expect(result[1].windDirection).toEqual(existingRows[1].windDirection)
  })
})

describe('filterRowsByModelType', () => {
  it('should return array of MoreCast2ForecastRows containing all rows that match the specified choice', () => {
    const rows = generateExistingRows()
    const result = filterRowsByModelType(rows, ModelChoice.GDPS)
    expect(result).toBeDefined()
    expect(result.length).toEqual(2)
  })
  it('should return an empty array if no rows match the specified choice', () => {
    const rows = generateExistingRows()
    const result = filterRowsByModelType(rows, ModelChoice.HRDPS)
    expect(result).toBeDefined()
    expect(result.length).toEqual(0)
  })
})
