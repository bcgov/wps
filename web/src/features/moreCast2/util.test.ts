import { DateTime } from 'luxon'
import { ModelChoice, ObservedDaily, StationPrediction } from 'api/moreCast2API'
import {
  createDateInterval,
  filterRowsByModelType,
  fillInTheModelBlanks,
  parseModelsForStationsHelper,
  replaceColumnValuesFromPrediction,
  rowIDHasher,
  buildListOfRowsToDisplay,
  marshalAllMoreCast2ForecastRowsByStationAndDate,
  parseObservedDailiesForStationsHelper,
  buildYesterdayDailiesFromObserved
} from 'features/moreCast2/util'
import { MoreCast2ForecastRow } from 'features/moreCast2/interfaces'
import { ColPrediction } from 'features/moreCast2/slices/columnModelSlice'
import { StationGroupMember } from 'api/stationAPI'

const TEST_NUMBER = 7
const TEST_MODEL = ModelChoice.HRDPS
const TEST_DATE = '2023-02-16T20:00:00+00:00'
const TEST_DATE2 = '2023-02-17T20:00:00+00:00'
const TEST_DATE3 = '2023-02-18T20:00:00+00:00'
const TEST_DATE4 = '2023-02-19T20:00:00+00:00'
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
    const existingRows: MoreCast2ForecastRow[] = generateRowsForTwoStations()

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
    const rows = generateRowsForTwoStations()
    const result = filterRowsByModelType(rows, ModelChoice.GDPS)
    expect(result).toBeDefined()
    expect(result.length).toEqual(2)
  })
  it('should return an empty array if no rows match the specified choice', () => {
    const rows = generateRowsForTwoStations()
    const result = filterRowsByModelType(rows, ModelChoice.HRDPS)
    expect(result).toBeDefined()
    expect(result.length).toEqual(0)
  })
})

describe('buildListOfRowsToDisplay', () => {
  it('should prioritize Actuals higher than any other model type', () => {
    const extraRow: MoreCast2ForecastRow = {
      id: rowIDHasher(1, DateTime.fromISO(TEST_DATE3)),
      stationCode: 1,
      stationName: 'one',
      forDate: DateTime.fromISO(TEST_DATE3),
      temp: { value: 1, choice: ModelChoice.GDPS },
      rh: { value: 1, choice: ModelChoice.GDPS },
      precip: { value: 1, choice: ModelChoice.GDPS },
      windSpeed: { value: 1, choice: ModelChoice.GDPS },
      windDirection: { value: 1, choice: ModelChoice.GDPS }
    }

    let modelRows = generateRowsForTwoStations()
    modelRows = [...modelRows, extraRow]
    modelRows.forEach(row => (row.stationCode = 1))
    const observedRows = generateRowsWithActuals(1, 'one')
    const stationsDict = marshalAllMoreCast2ForecastRowsByStationAndDate(observedRows, modelRows)
    const stationGroupMember = generateStationGroupMember(1, 'one')
    const displayRows = buildListOfRowsToDisplay(stationsDict, [stationGroupMember])

    expect(displayRows.length).toEqual(3)
    expect(displayRows[0].rh.choice).toEqual(ModelChoice.ACTUAL)
    expect(displayRows[1].rh.choice).toEqual(ModelChoice.ACTUAL)
    expect(displayRows[2].rh.choice).toEqual(ModelChoice.GDPS)
  })
  it('should display exactly 1 row per station/date combo', () => {
    const observedRows1 = generateRowsWithActuals(1, 'one')
    const observedRows2 = generateRowsWithActuals(2, 'two')
    const modelRows1 = generateRowsForStation(1, 'one')
    const modelRows2 = generateRowsForStation(2, 'two')

    const stationDict = marshalAllMoreCast2ForecastRowsByStationAndDate(
      [...observedRows1, ...observedRows2],
      [...modelRows1, ...modelRows2]
    )
    const stationGroupMember1 = generateStationGroupMember(1, 'one')
    const stationGroupMember2 = generateStationGroupMember(2, 'two')
    const testStations = [stationGroupMember1, stationGroupMember2]
    const displayRows = buildListOfRowsToDisplay(stationDict, testStations)

    expect(displayRows.length).toEqual(6)

    const testDates = [TEST_DATE, TEST_DATE2, TEST_DATE3]

    testStations.forEach(station => {
      const results = displayRows.filter(row => row.stationCode === station.station_code)
      expect(results.length).toEqual(3)
      testDates.forEach(date => {
        // DateTime formatting is ugly but necessary to coalesce timezones consistently from TEST_DATE strings
        const dateResults = results.filter(row => row.forDate.toISO() === DateTime.fromISO(date).toISO())
        expect(dateResults.length).toEqual(1)
      })
    })
  })
  it('should sort rows in descending order by date', () => {
    const stationGroupMember = generateStationGroupMember(1, 'one')
    const observedRows = generateRowsWithActuals(stationGroupMember.station_code, stationGroupMember.display_label)
    const modelRows = generateRowsForStation(stationGroupMember.station_code, stationGroupMember.display_label)
    const stationDict = marshalAllMoreCast2ForecastRowsByStationAndDate(observedRows, modelRows)
    const displayRows = buildListOfRowsToDisplay(stationDict, [stationGroupMember])

    expect(displayRows.length).toEqual(3)
    expect(displayRows[0].forDate.toISO()).toEqual(DateTime.fromISO(TEST_DATE).toISO())
    expect(displayRows[1].forDate.toISO()).toEqual(DateTime.fromISO(TEST_DATE2).toISO())
    expect(displayRows[2].forDate.toISO()).toEqual(DateTime.fromISO(TEST_DATE3).toISO())
  })
})

describe('parseObservedDailiesForStationsHelper', () => {
  it('should sort alphabetically by station name', () => {
    const multipleObservations: ObservedDaily[] = [
      {
        id: '1',
        data_type: 'YESTERDAY',
        station_code: 2,
        station_name: 'alpha',
        utcTimestamp: DateTime.fromISO(TEST_DATE).toUTC().toMillis().toString(),
        temperature: 1,
        relative_humidity: 1,
        precipitation: 1,
        wind_direction: 1,
        wind_speed: 1
      },
      {
        id: '2',
        data_type: 'YESTERDAY',
        station_code: 1,
        station_name: 'omega',
        utcTimestamp: DateTime.fromISO(TEST_DATE).toUTC().toMillis().toString(),
        temperature: 2,
        relative_humidity: 2,
        precipitation: 2,
        wind_direction: 2,
        wind_speed: 2
      }
    ]

    const rows = parseObservedDailiesForStationsHelper(multipleObservations)
    expect(rows.length).toEqual(2)
    expect(rows[0].stationName).toEqual('alpha')
    expect(rows[1].stationName).toEqual('omega')
  })
})

describe('buildYesterdayDailiesFromObserved', () => {
  it('should correctly create yesterdays as ObservedDaily[] for future dates based on a prior observed date', () => {
    const observations: ObservedDaily[] = [
      {
        id: '1',
        data_type: 'ACTUAL',
        station_code: 1,
        station_name: 'alpha',
        utcTimestamp: DateTime.fromISO(TEST_DATE).toMillis().toString(),
        temperature: 1,
        relative_humidity: 1,
        precipitation: 1,
        wind_direction: 1,
        wind_speed: 1
      },
      {
        id: '2',
        data_type: 'ACTUAL',
        station_code: 1,
        station_name: 'alpha',
        utcTimestamp: DateTime.fromISO(TEST_DATE2).toMillis().toString(),
        temperature: 2,
        relative_humidity: 2,
        precipitation: 2,
        wind_direction: 2,
        wind_speed: 2
      }
    ]
    const yesterdays = buildYesterdayDailiesFromObserved(observations, DateTime.fromISO(TEST_DATE4).toISODate())
    console.log(yesterdays)

    expect(yesterdays.length).toEqual(2)
    // values should come from most recent ObservedDaily
    expect(yesterdays[0].temperature).toEqual(2)
    expect(yesterdays[0].relative_humidity).toEqual(2)
    expect(yesterdays[0].utcTimestamp).toEqual(DateTime.fromISO(TEST_DATE3).toMillis().toString())

    expect(yesterdays[1].temperature).toEqual(2)
    expect(yesterdays[1].relative_humidity).toEqual(2)
    expect(yesterdays[1].utcTimestamp).toEqual(DateTime.fromISO(TEST_DATE4).toMillis().toString())
  })
})
