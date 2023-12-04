import { DateTime } from 'luxon'
import { ModelChoice } from 'api/moreCast2API'
import {
  createDateInterval,
  createWeatherModelLabel,
  fillGrassCuring,
  mapForecastChoiceLabels,
  parseForecastsHelper,
  rowIDHasher,
  validActualPredicate,
  validForecastPredicate
} from 'features/moreCast2/util'
import { buildValidActualRow, buildValidForecastRow } from 'features/moreCast2/rowFilters.test'

const TEST_DATE = '2023-02-16T20:00:00+00:00'
const TEST_DATE2 = '2023-02-17T20:00:00+00:00'
const TEST_CODE = 209
const TEST_DATETIME = DateTime.fromISO(TEST_DATE)

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
    for_date: Date.parse('2022-01-02T10:00:00.000Z'),
    precip: 1,
    rh: 1,
    temp: 1,
    wind_direction: 1,
    wind_speed: 1,
    grass_curing: 1
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
        id: '12022-01-02',
        forDate: DateTime.fromMillis(Date.parse('2022-01-02T10:00:00.000Z')),
        precip: { choice: ModelChoice.FORECAST, value: 1 },
        rh: { choice: ModelChoice.FORECAST, value: 1 },
        stationCode: 1,
        stationName: 'one',
        temp: { choice: ModelChoice.FORECAST, value: 1 },
        windDirection: { choice: ModelChoice.FORECAST, value: 1 },
        windSpeed: { choice: ModelChoice.FORECAST, value: 1 },
        grassCuring: 1
      },
      {
        id: '22022-01-02',
        forDate: DateTime.fromMillis(Date.parse('2022-01-02T10:00:00.000Z')),
        precip: { choice: ModelChoice.FORECAST, value: 1 },
        rh: { choice: ModelChoice.FORECAST, value: 1 },
        stationCode: 2,
        stationName: 'two',
        temp: { choice: ModelChoice.FORECAST, value: 1 },
        windDirection: { choice: ModelChoice.FORECAST, value: 1 },
        windSpeed: { choice: ModelChoice.FORECAST, value: 1 },
        grassCuring: 1
      }
    ])
  })
  it('should handle case where station is not found in station member list', () => {
    const result = parseForecastsHelper([buildForecastRecord(1)], [])
    expect(result).toEqual([
      {
        id: '12022-01-02',
        forDate: DateTime.fromMillis(Date.parse('2022-01-02T10:00:00.000Z')),
        precip: { choice: ModelChoice.FORECAST, value: 1 },
        rh: { choice: ModelChoice.FORECAST, value: 1 },
        stationCode: 1,
        stationName: '',
        temp: { choice: ModelChoice.FORECAST, value: 1 },
        windDirection: { choice: ModelChoice.FORECAST, value: 1 },
        windSpeed: { choice: ModelChoice.FORECAST, value: 1 },
        grassCuring: 1
      }
    ])
  })
  it('should handle case where forecast parameters are missing', () => {
    const result = parseForecastsHelper(
      [
        {
          ...buildForecastRecord(1),
          precip: NaN,
          rh: NaN,
          temp: NaN,
          wind_speed: NaN,
          wind_direction: NaN,
          grass_curing: NaN
        }
      ],
      [buildStationGroupMember('1', 1, 'one', '1', '1')]
    )
    expect(result).toEqual([
      {
        id: '12022-01-02',
        forDate: DateTime.fromMillis(Date.parse('2022-01-02T10:00:00.000Z')),
        precip: { choice: ModelChoice.FORECAST, value: NaN },
        rh: { choice: ModelChoice.FORECAST, value: NaN },
        stationCode: 1,
        stationName: 'one',
        temp: { choice: ModelChoice.FORECAST, value: NaN },
        windDirection: { choice: ModelChoice.FORECAST, value: NaN },
        windSpeed: { choice: ModelChoice.FORECAST, value: NaN },
        grassCuring: NaN
      }
    ])
  })
})
describe('createWeatherModelLabel', () => {
  it('should not alter non-bias adjusted model label', () => {
    const result = createWeatherModelLabel(ModelChoice.GDPS)
    expect(result).toBe(ModelChoice.GDPS)
  })
  it('should format bias adjusted model label', () => {
    const result = createWeatherModelLabel(ModelChoice.GDPS_BIAS)
    expect(result).toBe('GDPS bias')
  })
})
describe('validActualPredicate', () => {
  const row = buildValidActualRow(123, TEST_DATETIME)
  it('should return true if a row contains valid Actual values', () => {
    const result = validActualPredicate(row)
    expect(result).toBe(true)
  })
  it('should return false if a row does not contain valid Actual values', () => {
    row.precipActual = NaN
    const result = validActualPredicate(row)
    expect(result).toBe(false)
  })
})
describe('validForecastPredicate', () => {
  const row = buildValidForecastRow(123, TEST_DATETIME, 'FORECAST')
  it('should return true if a row contains valid Forecast values', () => {
    const result = validForecastPredicate(row)
    expect(result).toBe(true)
  })
  it('should return false if a row does not contain valid Forecast values', () => {
    row.precipForecast = undefined
    const result = validForecastPredicate(row)
    expect(result).toBe(false)
  })
})
describe('mapForecastChoiceLabels', () => {
  const forecast1A = buildValidForecastRow(123, TEST_DATETIME, 'FORECAST')
  const forecast1B = buildValidForecastRow(123, TEST_DATETIME.plus({ days: 1 }), 'FORECAST')
  const newRows = [forecast1A, forecast1B]

  const forecast2A = buildValidForecastRow(123, TEST_DATETIME, 'GDPS')
  const forecast2B = buildValidForecastRow(123, TEST_DATETIME.plus({ days: 1 }), 'MANUAL')
  forecast2A.tempForecast!.choice = 'HRDPS'
  forecast2B.precipForecast!.choice = 'GFS'
  const storedRows = [forecast2A, forecast2B]

  it('should map the correct label to the correct row', () => {
    const labelledRows = mapForecastChoiceLabels(newRows, storedRows)
    expect(labelledRows[0].tempForecast!.choice).toBe('HRDPS')
    expect(labelledRows[0].precipForecast!.choice).toBe('GDPS')
    expect(labelledRows[1].precipForecast!.choice).toBe('GFS')
    expect(labelledRows[1].rhForecast!.choice).toBe('MANUAL')
  })
})
describe('fillGrassCuring', () => {
  const forecast1A = buildValidForecastRow(123, TEST_DATETIME, 'FORECAST')
  const forecast2A = buildValidForecastRow(321, TEST_DATETIME, 'FORECAST')
  const forecast3A = buildValidForecastRow(111, TEST_DATETIME, 'FORECAST')
  const actual1A = buildValidActualRow(123, TEST_DATETIME.minus({ days: 1 }))
  const actual2A = buildValidActualRow(321, TEST_DATETIME.minus({ days: 1 }))
  const actual3A = buildValidActualRow(111, TEST_DATETIME.minus({ days: 1 }))
  actual1A.grassCuring = 80
  actual2A.grassCuring = 70

  const actual1B = buildValidActualRow(123, TEST_DATETIME.minus({ days: 2 }))
  const actual2B = buildValidActualRow(321, TEST_DATETIME.minus({ days: 2 }))
  actual1B.grassCuring = 8
  actual2B.grassCuring = 7

  const rows = [forecast1A, forecast2A, forecast3A, actual1A, actual1B, actual2A, actual2B, actual3A]

  it('should map the most recent grass curing value for each station to each forecast', () => {
    const filledRows = fillGrassCuring(rows)
    expect(filledRows[0].grassCuring).toBe(80)
    expect(filledRows[1].grassCuring).toBe(70)
    expect(filledRows[2].grassCuring).toBe(NaN)
  })
})
