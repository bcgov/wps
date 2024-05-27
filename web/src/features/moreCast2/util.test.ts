import { DateTime } from 'luxon'
import { ModelChoice } from 'api/moreCast2API'
import {
  createDateInterval,
  createWeatherModelLabel,
  fillGrassCuringForecast,
  fillGrassCuringCWFIS,
  fillStationGrassCuringForward,
  mapForecastChoiceLabels,
  parseForecastsHelper,
  rowIDHasher,
  validActualPredicate,
  validForecastPredicate,
  fillForecastsFromRows,
  dateTimeComparator,
  calculateFWIs,
  simulateFireWeatherIndices
} from 'features/moreCast2/util'
import { buildValidActualRow, buildValidForecastRow } from 'features/moreCast2/rowFilters.test'
import { createEmptyMoreCast2Row } from 'features/moreCast2/slices/dataSlice'
import { MoreCast2Row } from 'features/moreCast2/interfaces'

const TEST_DATE = '2023-02-16T20:00:00+00:00'
const TEST_DATE2 = '2023-02-17T20:00:00+00:00'
const TEST_CODE = 209
const TEST_DATETIME = DateTime.fromISO(TEST_DATE)
const YESTERDAY = DateTime.now().plus({ days: -1 })
const TODAY = DateTime.now()
const TOMORROW = DateTime.now().plus({ days: 1 })

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
        grassCuring: { choice: ModelChoice.FORECAST, value: 1 }
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
        grassCuring: { choice: ModelChoice.FORECAST, value: 1 }
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
        grassCuring: { choice: ModelChoice.FORECAST, value: 1 }
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
        grassCuring: { choice: ModelChoice.FORECAST, value: NaN }
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

const forecast1A = buildValidForecastRow(123, TEST_DATETIME, 'FORECAST')
const forecast1B = buildValidForecastRow(123, TEST_DATETIME.plus({ days: 1 }), 'FORECAST')
const forecast1C = buildValidForecastRow(123, TEST_DATETIME.plus({ days: 2 }), 'FORECAST')
const forecast2A = buildValidForecastRow(321, TEST_DATETIME, 'FORECAST')
const forecast3A = buildValidForecastRow(111, TEST_DATETIME, 'FORECAST')
const actual1A = buildValidActualRow(123, TEST_DATETIME.minus({ days: 1 }))
const actual2A = buildValidActualRow(321, TEST_DATETIME.minus({ days: 1 }))
const actual3A = buildValidActualRow(111, TEST_DATETIME.minus({ days: 1 }))
actual1A.grassCuringActual = 80
actual2A.grassCuringActual = 70

const actual1B = buildValidActualRow(123, TEST_DATETIME.minus({ days: 2 }))
const actual2B = buildValidActualRow(321, TEST_DATETIME.minus({ days: 2 }))
actual1B.grassCuringActual = 8
actual2B.grassCuringActual = 7

const rows = [
  forecast1A,
  forecast1B,
  forecast1C,
  forecast2A,
  forecast3A,
  actual1A,
  actual1B,
  actual2A,
  actual2B,
  actual3A
]

describe('fillGrassCuringCWFIS', () => {
  it('should map the most recent CWFIS grass curing value to all future rows', () => {
    forecast1A.grassCuringCWFIS!.value = 50
    fillGrassCuringCWFIS(rows)
    expect(forecast1A.grassCuringCWFIS!.value).toBe(50)
    expect(forecast1B.grassCuringCWFIS!.value).toBe(50)
    expect(forecast1C.grassCuringCWFIS!.value).toBe(50)
  })
  it('should not map the most recent CWFIS grass curing value to past rows', () => {
    forecast1A.grassCuringCWFIS!.value = NaN
    forecast1B.grassCuringCWFIS!.value = 50
    fillGrassCuringCWFIS(rows)
    expect(forecast1A.grassCuringCWFIS!.value).toBe(NaN)
    expect(forecast1B.grassCuringCWFIS!.value).toBe(50)
  })
  it('should not map CWFIS values from one station to another station', () => {
    forecast1A.grassCuringCWFIS!.value = 50
    forecast1B.grassCuringCWFIS!.value = NaN
    fillGrassCuringCWFIS(rows)
    expect(forecast2A.grassCuringCWFIS!.value).toBe(NaN)
    expect(forecast3A.grassCuringCWFIS!.value).toBe(NaN)
  })
})

describe('fillGrassCuringForecast', () => {
  it('should map the most recent grass curing value for each station to each forecast, without overwriting existing submitted values', () => {
    forecast1A.grassCuringForecast!.value = NaN
    forecast1B.grassCuringForecast!.value = 50
    fillGrassCuringForecast(rows)
    expect(forecast1A.grassCuringForecast!.value).toBe(NaN)
    expect(forecast1B.grassCuringForecast!.value).toBe(50)
    expect(forecast1C.grassCuringForecast!.value).toBe(50)
    expect(forecast2A.grassCuringForecast!.value).toBe(70)
    expect(forecast3A.grassCuringForecast!.value).toBe(NaN)
  })
  it('should not update values in the past', () => {
    forecast1A.grassCuringForecast!.value = 60
    forecast1B.grassCuringForecast!.value = 50
    fillGrassCuringForecast(rows)
    expect(forecast1A.grassCuringForecast!.value).toBe(60)
    expect(forecast1B.grassCuringForecast!.value).toBe(50)
    expect(forecast1C.grassCuringForecast!.value).toBe(50)
    expect(forecast2A.grassCuringForecast!.value).toBe(70)
    expect(forecast3A.grassCuringForecast!.value).toBe(NaN)
  })
})
describe('fillStationGrassCuringForward', () => {
  it('should fill grass curing forward for each station if a row is edited', () => {
    forecast1B.grassCuringForecast!.value = 43
    fillStationGrassCuringForward(forecast1B, rows)
    expect(forecast1C.grassCuringForecast!.value).toBe(43)
    expect(forecast1A.grassCuringForecast!.value).toBe(60)
    expect(forecast2A.grassCuringForecast!.value).toBe(70)
  })
})
describe('fillRowsFromSavedDraft', () => {
  it('should fill forecast rows from saved drafts', () => {
    const tomorrow = DateTime.now().plus({ days: 1 })
    const stationCode = 1
    const id = rowIDHasher(stationCode, tomorrow)
    const savedRows = buildValidForecastRow(stationCode, tomorrow, 'MANUAL')
    const rowsToFill = createEmptyMoreCast2Row(id, stationCode, 'station', tomorrow, 1, 1)

    const filledRows = fillForecastsFromRows([rowsToFill], [savedRows])
    expect(filledRows[0].tempForecast?.value).toBe(2)
    expect(filledRows[0].tempForecast?.choice).toBe(ModelChoice.MANUAL)
  })
  it('should not fill rows if they contain actuals', () => {
    const tomorrow = DateTime.now()
    const stationCode = 1
    const id = rowIDHasher(stationCode, tomorrow)
    const savedRows = buildValidActualRow(stationCode, tomorrow)
    const rowsToFill = createEmptyMoreCast2Row(id, stationCode, 'station', tomorrow, 1, 1)

    const filledRows = fillForecastsFromRows([rowsToFill], [savedRows])
    expect(filledRows[0].tempForecast?.value).toBe(undefined)
    expect(filledRows[0].tempForecast?.choice).toBe(undefined)
  })
  it('should not fill rows if they are in the past', () => {
    const tomorrow = DateTime.now().minus({ days: 2 })
    const stationCode = 1
    const id = rowIDHasher(stationCode, tomorrow)
    const savedRows = buildValidActualRow(stationCode, tomorrow)
    const rowsToFill = createEmptyMoreCast2Row(id, stationCode, 'station', tomorrow, 1, 1)

    const filledRows = fillForecastsFromRows([rowsToFill], [savedRows])
    expect(filledRows[0].tempForecast?.value).toBe(undefined)
    expect(filledRows[0].tempForecast?.choice).toBe(undefined)
  })
})

describe('dateTimeComparator', () => {
  it('should return correct value when first date before second date', () => {
    const first = DateTime.now()
    const second = first.plus({ days: 1 })
    const result = dateTimeComparator(first, second)
    expect(result).toBe(-1)
  })
  it('should return correct value when first date after second date', () => {
    const first = DateTime.now()
    const second = first.plus({ days: -1 })
    const result = dateTimeComparator(first, second)
    expect(result).toBe(1)
  })
  it('should return correct value when first date and second date are the same', () => {
    const first = DateTime.now()
    const result = dateTimeComparator(first, first)
    expect(result).toBe(0)
  })
})

/** Begin helper functions for calculateFWIs tests */

const populateActualRowWithFWIs = (row: MoreCast2Row, dc: number, dmc: number, ffmc: number): MoreCast2Row => {
  row.dcCalcActual = dc
  row.dmcCalcActual = dmc
  row.ffmcCalcActual = ffmc
  return row
}
const populateForecastRowWithFWIs = (row: MoreCast2Row, dc: number, dmc: number, ffmc: number): MoreCast2Row => {
  row.dcCalcForecast = { choice: ModelChoice.NULL, value: dc }
  row.dmcCalcForecast = { choice: ModelChoice.NULL, value: dmc }
  row.ffmcCalcForecast = { choice: ModelChoice.NULL, value: ffmc }
  return row
}

const buildActualRowWithIndices = (
  stationCode: number,
  forDate: DateTime,
  dc: number = NaN,
  dmc: number = NaN,
  ffmc: number = NaN
): MoreCast2Row => {
  let actualRow = buildValidActualRow(stationCode, forDate)
  actualRow = populateActualRowWithFWIs(actualRow, dc, dmc, ffmc)
  return actualRow
}

const buildForecastRowWithIndices = (
  stationCode: number,
  forDate: DateTime,
  dc: number = NaN,
  dmc: number = NaN,
  ffmc: number = NaN
): MoreCast2Row => {
  let forecastRow = buildValidForecastRow(stationCode, forDate)
  forecastRow = populateForecastRowWithFWIs(forecastRow, dc, dmc, ffmc)
  return forecastRow
}
/** End helper functions for calculateFWIs tests */

describe('calculateFWIs', () => {
  it('should populate forecast FWIS for forecast from actual', () => {
    const actualRow = buildActualRowWithIndices(1, YESTERDAY, 438, 89, 87)
    let forecastRow = buildValidForecastRow(1, TODAY)
    forecastRow = calculateFWIs(actualRow, forecastRow)
    expect(forecastRow.buiCalcForecast!.choice).toBe(ModelChoice.NULL)
    expect(forecastRow.dcCalcForecast!.choice).toBe(ModelChoice.NULL)
    expect(forecastRow.dmcCalcForecast!.choice).toBe(ModelChoice.NULL)
    expect(forecastRow.ffmcCalcForecast!.choice).toBe(ModelChoice.NULL)
    expect(forecastRow.isiCalcForecast!.choice).toBe(ModelChoice.NULL)
    expect(forecastRow.fwiCalcForecast!.choice).toBe(ModelChoice.NULL)
    expect(forecastRow.buiCalcForecast!.value).toBeCloseTo(108.5, 1)
    expect(forecastRow.dcCalcForecast!.value).toBeCloseTo(439.6, 1)
    expect(forecastRow.dmcCalcForecast!.value).toBeCloseTo(78.4, 1)
    expect(forecastRow.ffmcCalcForecast!.value).toBeCloseTo(75.9, 1)
    expect(forecastRow.isiCalcForecast!.value).toBeCloseTo(0.9, 1)
    expect(forecastRow.fwiCalcForecast!.value).toBeCloseTo(4.7, 1)
  })
  it('should populate forecast FWIS for forecast from another forecast', () => {
    const yesterdayForecastRow = buildForecastRowWithIndices(1, YESTERDAY, 438, 89, 87)
    let forecastRow = buildValidForecastRow(1, TODAY)
    forecastRow = calculateFWIs(yesterdayForecastRow, forecastRow)
    expect(forecastRow.buiCalcForecast!.choice).toBe(ModelChoice.NULL)
    expect(forecastRow.dcCalcForecast!.choice).toBe(ModelChoice.NULL)
    expect(forecastRow.dmcCalcForecast!.choice).toBe(ModelChoice.NULL)
    expect(forecastRow.ffmcCalcForecast!.choice).toBe(ModelChoice.NULL)
    expect(forecastRow.isiCalcForecast!.choice).toBe(ModelChoice.NULL)
    expect(forecastRow.fwiCalcForecast!.choice).toBe(ModelChoice.NULL)
    expect(forecastRow.buiCalcForecast!.value).toBeCloseTo(108.5, 1)
    expect(forecastRow.dcCalcForecast!.value).toBeCloseTo(439.6, 1)
    expect(forecastRow.dmcCalcForecast!.value).toBeCloseTo(78.4, 1)
    expect(forecastRow.ffmcCalcForecast!.value).toBeCloseTo(75.9, 1)
    expect(forecastRow.isiCalcForecast!.value).toBeCloseTo(0.9, 1)
    expect(forecastRow.fwiCalcForecast!.value).toBeCloseTo(4.7, 1)
  })
  it("should not calculate ffmc, isi, bui or fwi if ffmc in yesterday's actual row is NaN", () => {
    const yesterdayForecastRow = buildForecastRowWithIndices(1, YESTERDAY, 438, 89, NaN)
    let forecastRow = buildValidForecastRow(1, TODAY)
    forecastRow = calculateFWIs(yesterdayForecastRow, forecastRow)
    expect(forecastRow.ffmcCalcForecast).toBe(undefined)
    expect(forecastRow.isiCalcForecast).toBe(undefined)
    expect(forecastRow.fwiCalcForecast).toBe(undefined)
  })
  it("should not calculate ffmc, isi, bui or fwi if ffmc in yesterday's forecast row is NaN", () => {
    const yesterdayForecastRow = buildForecastRowWithIndices(1, YESTERDAY, 438, 89, NaN)
    let forecastRow = buildValidForecastRow(1, TODAY)
    forecastRow = calculateFWIs(yesterdayForecastRow, forecastRow)
    expect(forecastRow.ffmcCalcForecast).toBe(undefined)
    expect(forecastRow.isiCalcForecast).toBe(undefined)
    expect(forecastRow.fwiCalcForecast).toBe(undefined)
  })
  it("should not calculate dmc, bui, fwi if dmc in yesterday's actual row is NaN", () => {
    const yesterdayForecastRow = buildForecastRowWithIndices(1, YESTERDAY, 438, NaN, 87)
    let forecastRow = buildValidForecastRow(1, TODAY)
    forecastRow = calculateFWIs(yesterdayForecastRow, forecastRow)
    expect(forecastRow.dmcCalcForecast).toBe(undefined)
    expect(forecastRow.buiCalcForecast).toBe(undefined)
    expect(forecastRow.fwiCalcForecast).toBe(undefined)
  })
  it("sshould not calculate dmc, bui, fwi if dmc in yesterday's forecast row is NaN", () => {
    const yesterdayForecastRow = buildForecastRowWithIndices(1, YESTERDAY, 438, NaN, 87)
    let forecastRow = buildValidForecastRow(1, TODAY)
    forecastRow = calculateFWIs(yesterdayForecastRow, forecastRow)
    expect(forecastRow.dmcCalcForecast).toBe(undefined)
    expect(forecastRow.buiCalcForecast).toBe(undefined)
    expect(forecastRow.fwiCalcForecast).toBe(undefined)
  })
  it("should not calculate dc, bui, fwi if dmc in yesterday's actual row is NaN", () => {
    const yesterdayForecastRow = buildForecastRowWithIndices(1, YESTERDAY, NaN, 89, 87)
    let forecastRow = buildValidForecastRow(1, TODAY)
    forecastRow = calculateFWIs(yesterdayForecastRow, forecastRow)
    expect(forecastRow.dcCalcForecast).toBe(undefined)
    expect(forecastRow.buiCalcForecast).toBe(undefined)
    expect(forecastRow.fwiCalcForecast).toBe(undefined)
  })
  it("sshould not calculate dc, bui, fwi if dmc in yesterday's forecast row is NaN", () => {
    const yesterdayForecastRow = buildForecastRowWithIndices(1, YESTERDAY, NaN, 89, 87)
    let forecastRow = buildValidForecastRow(1, TODAY)
    forecastRow = calculateFWIs(yesterdayForecastRow, forecastRow)
    expect(forecastRow.dcCalcForecast).toBe(undefined)
    expect(forecastRow.buiCalcForecast).toBe(undefined)
    expect(forecastRow.fwiCalcForecast).toBe(undefined)
  })
})

describe('simulateFireWeatherIndices', () => {
  it('should return input unchanged if only one row present per station', () => {
    const forecastRow = buildValidForecastRow(1, TODAY)
    const result = simulateFireWeatherIndices([forecastRow])
    expect(result[0]).toBe(forecastRow)
  })
  it('should simulate FWIs for all forecast rows', () => {
    const forecastRowA = buildForecastRowWithIndices(1, YESTERDAY, 438, 89, 87)
    const forecastRowB = buildValidForecastRow(1, TODAY)
    const forecastRowC = buildValidForecastRow(1, TOMORROW)
    forecastRowC.tempForecast!.value = 27
    const result = simulateFireWeatherIndices([forecastRowA, forecastRowB, forecastRowC])
    expect(result.length).toBe(3)
    expect(result[0]).toBe(forecastRowA)
    expect(forecastRowB.buiCalcForecast!.value).toBeCloseTo(108.5, 1)
    expect(forecastRowB.dcCalcForecast!.value).toBeCloseTo(439.6, 1)
    expect(forecastRowB.dmcCalcForecast!.value).toBeCloseTo(78.4, 1)
    expect(forecastRowB.ffmcCalcForecast!.value).toBeCloseTo(75.9, 1)
    expect(forecastRowB.isiCalcForecast!.value).toBeCloseTo(0.9, 1)
    expect(forecastRowB.fwiCalcForecast!.value).toBeCloseTo(4.7, 1)
    expect(forecastRowC.buiCalcForecast!.value).toBeCloseTo(104.7, 1)
    expect(forecastRowC.dcCalcForecast!.value).toBeCloseTo(445.6, 1)
    expect(forecastRowC.dmcCalcForecast!.value).toBeCloseTo(74.2, 1)
    expect(forecastRowC.ffmcCalcForecast!.value).toBeCloseTo(89.3, 1)
    expect(forecastRowC.isiCalcForecast!.value).toBeCloseTo(4.3, 1)
    expect(forecastRowC.fwiCalcForecast!.value).toBeCloseTo(17.8, 1)
  })
  it('should simulate FWIs for multiple stations', () => {
    const station1ForecastA = buildForecastRowWithIndices(1, TODAY, 438, 89, 87)
    const station2ForecastA = buildForecastRowWithIndices(2, TODAY, 445, 91, 85)
    const station1ForecastB = buildValidForecastRow(1, TOMORROW)
    const station2ForecastB = buildValidForecastRow(2, TOMORROW)
    const result = simulateFireWeatherIndices([
      station1ForecastB,
      station2ForecastA,
      station1ForecastA,
      station2ForecastB
    ])
    expect(result.filter(row => row.stationCode === 1 && row.forDate === TODAY)[0]).toBe(station1ForecastA)
    expect(result.filter(row => row.stationCode === 2 && row.forDate === TODAY)[0]).toBe(station2ForecastA)
    const station1Bresult = result.filter(row => row.stationCode === 1 && row.forDate === TOMORROW)[0]
    expect(station1Bresult.buiCalcForecast!.value).toBeCloseTo(108.5, 1)
    expect(station1Bresult.dcCalcForecast!.value).toBeCloseTo(439.6, 1)
    expect(station1Bresult.dmcCalcForecast!.value).toBeCloseTo(78.4, 1)
    expect(station1Bresult.ffmcCalcForecast!.value).toBeCloseTo(75.9, 1)
    expect(station1Bresult.isiCalcForecast!.value).toBeCloseTo(0.9, 1)
    expect(station1Bresult.fwiCalcForecast!.value).toBeCloseTo(4.7, 1)
    const station2Bresult = result.filter(row => row.stationCode === 2 && row.forDate === TOMORROW)[0]
    expect(station2Bresult.buiCalcForecast!.value).toBeCloseTo(110.5, 1)
    expect(station2Bresult.dcCalcForecast!.value).toBeCloseTo(446.6, 1)
    expect(station2Bresult.dmcCalcForecast!.value).toBeCloseTo(80.0, 1)
    expect(station2Bresult.ffmcCalcForecast!.value).toBeCloseTo(75.1, 1)
    expect(station2Bresult.isiCalcForecast!.value).toBeCloseTo(0.9, 1)
    expect(station2Bresult.fwiCalcForecast!.value).toBeCloseTo(4.5, 1)
  })
  it('should not use old actuals when multiple actuals present', () => {
    const yesterdayForecastRow = buildActualRowWithIndices(1, YESTERDAY, 445, 91, 85)
    const todayForecastRow = buildActualRowWithIndices(1, TODAY, 438, 89, 87)
    const tomorrowForecastRow = buildValidForecastRow(1, TOMORROW)
    const result = simulateFireWeatherIndices([yesterdayForecastRow, todayForecastRow, tomorrowForecastRow])
    const yesterdayResult = result.filter(row => row.forDate === YESTERDAY)[0]
    const todayResult = result.filter(row => row.forDate === TODAY)[0]
    const tomorrowResult = result.filter(row => row.forDate === TOMORROW)[0]
    expect(yesterdayResult).toEqual(yesterdayForecastRow)
    expect(todayResult).toEqual(todayForecastRow)
    expect(tomorrowResult.buiCalcForecast!.value).toBeCloseTo(108.5, 1)
    expect(tomorrowResult.dcCalcForecast!.value).toBeCloseTo(439.6, 1)
    expect(tomorrowResult.dmcCalcForecast!.value).toBeCloseTo(78.4, 1)
    expect(tomorrowResult.ffmcCalcForecast!.value).toBeCloseTo(75.9, 1)
    expect(tomorrowResult.isiCalcForecast!.value).toBeCloseTo(0.9, 1)
    expect(tomorrowResult.fwiCalcForecast!.value).toBeCloseTo(4.7, 1)
  })
})
