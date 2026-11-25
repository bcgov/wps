import type { ClimatologyDay, ClimatologySeries } from '@wps/api/climatologyAPI'
import {
  axisLabel,
  buildClimatologyRows,
  type ClimatologyRow,
  FIRE_SEASON,
  FULL_YEAR,
  formatDay,
  formatMonth,
  formatRange,
  formatValue,
  latestRow,
  MIN_WINDOW_DAYS,
  maxZoom,
  monthStarts,
  rowsExtent,
  rowsInWindow,
  snapToRows,
  todayOnChart,
  valueExtent,
  variableInSentence,
  visibleWindow,
  widenWindow,
  windowTicks
} from './climatologyRows'

const day = (month: number, dayOfMonth: number, median = 15): ClimatologyDay => ({
  month,
  day: dayOfMonth,
  count: 30,
  station_count: 1,
  minimum: 2,
  p25: 10,
  median,
  p75: 20,
  p90: 25,
  maximum: 33
})

const series = (overrides: Partial<ClimatologySeries> = {}): ClimatologySeries => ({
  station_codes: [322],
  first_reference_year: 1990,
  last_reference_year: 2025,
  days: [day(3, 31), day(4, 1), day(7, 1, 22), day(10, 31), day(11, 1)],
  observations: [
    { date: '2026-04-01', value: 8.5, station_count: 1 },
    { date: '2026-11-01', value: 3, station_count: 1 }
  ],
  compared_years: [],
  ...overrides
})

describe('buildClimatologyRows', () => {
  it('keeps the days in the months asked for, in order, dated in the selected year', () => {
    const rows = buildClimatologyRows(series(), 2026, FIRE_SEASON)

    expect(rows.map(row => new Date(row.time).toISOString().slice(0, 10))).toEqual([
      '2026-04-01',
      '2026-07-01',
      '2026-10-31'
    ])
  })

  it('carries the distribution and the observation of the same day', () => {
    const [first, second] = buildClimatologyRows(series(), 2026, FIRE_SEASON)

    expect(first).toMatchObject({
      minimum: 2,
      p25: 10,
      median: 15,
      p75: 20,
      p90: 25,
      maximum: 33,
      count: 30,
      stationCount: 1
    })
    expect(first.value).toBe(8.5)
    expect(first.valueStationCount).toBe(1)
    expect(second.median).toBe(22)
  })

  it('has no value on a day the selected year has not observed', () => {
    const rows = buildClimatologyRows(series(), 2026, FIRE_SEASON)

    expect(rows[1].value).toBeNull()
    expect(rows[1].valueStationCount).toBeNull()
  })

  it('carries the values of the compared years that have one for the day', () => {
    const compared_years = [
      { year: 2023, observations: [{ date: '2023-07-01', value: 31, station_count: 1 }] },
      {
        year: 2017,
        observations: [
          { date: '2017-04-01', value: 5, station_count: 1 },
          { date: '2017-07-01', value: 28, station_count: 1 }
        ]
      }
    ]

    const rows = buildClimatologyRows(series({ compared_years }), 2026, FIRE_SEASON)

    expect(rows.map(row => row.compared)).toEqual([{ 2017: 5 }, { 2023: 31, 2017: 28 }, {}])
  })

  it('shows every month for the full year', () => {
    expect(buildClimatologyRows(series(), 2026, FULL_YEAR)).toHaveLength(5)
  })

  it('has no rows without history', () => {
    expect(buildClimatologyRows(series({ days: [] }), 2026, FULL_YEAR)).toEqual([])
  })
})

describe('monthStarts', () => {
  it('is the first day of each month in the range', () => {
    const starts = monthStarts(2026, FIRE_SEASON)

    expect(starts).toHaveLength(7)
    expect(starts.map(formatMonth)).toEqual(['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct'])
    expect(new Date(starts[0]).toISOString()).toBe('2026-04-01T00:00:00.000Z')
  })
})

describe('formatting', () => {
  it('formats a day without the year', () => {
    expect(formatDay(Date.UTC(2026, 6, 7))).toBe('Jul 7')
  })

  it('formats a value with its unit', () => {
    expect(formatValue(21.26, 'temperature')).toBe('21.3°C')
    expect(formatValue(41.6, 'relative_humidity')).toBe('42%')
    expect(formatValue(12, 'wind_speed')).toBe('12.0 km/h')
    expect(formatValue(0.25, 'precipitation')).toBe('0.3 mm')
  })

  it('gives an index without a unit', () => {
    expect(formatValue(88.46, 'ffmc')).toBe('88.5')
    expect(formatValue(412.4, 'dc')).toBe('412')
  })
})

describe('variable labels', () => {
  it('lowers the case of a name in a sentence, but not of an acronym', () => {
    expect(variableInSentence('relative_humidity')).toBe('relative humidity')
    expect(variableInSentence('bui')).toBe('BUI')
  })

  it('labels an axis with the unit, if there is one', () => {
    expect(axisLabel('temperature')).toBe('Temperature (°C)')
    expect(axisLabel('fwi')).toBe('FWI')
  })
})

describe('todayOnChart', () => {
  const rows = buildClimatologyRows(series(), 2026, FIRE_SEASON)

  it('is today when it is within the rows of the current year', () => {
    expect(todayOnChart(rows, 2026, new Date(2026, 6, 7, 15))).toBe(Date.UTC(2026, 6, 7))
  })

  it('is nothing outside the rows shown', () => {
    expect(todayOnChart(rows, 2026, new Date(2026, 10, 17))).toBeNull()
  })

  it('is nothing for another year, or with no rows', () => {
    expect(todayOnChart(rows, 2025, new Date(2026, 6, 7))).toBeNull()
    expect(todayOnChart([], 2026, new Date(2026, 6, 7))).toBeNull()
  })
})

const DAY = 24 * 60 * 60 * 1000
const APRIL_1 = Date.UTC(2026, 3, 1)
const dayRows = (days: number[]): ClimatologyRow[] =>
  days.map(day => ({
    time: APRIL_1 + day * DAY,
    count: 30,
    minimum: 0,
    p25: 1,
    median: 2,
    p75: 3,
    p90: 4,
    maximum: 5,
    value: null,
    stationCount: 1,
    valueStationCount: null,
    compared: {}
  }))

describe('date windows', () => {
  const rows = dayRows([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19])
  const extent = { start: APRIL_1, end: APRIL_1 + 19 * DAY }

  it('spans the first to last row', () => {
    expect(rowsExtent(rows)).toEqual(extent)
    expect(rowsExtent([])).toBeNull()
  })

  it('shows the chosen window while it fits the rows, else every day', () => {
    const chosen = { start: APRIL_1 + 2 * DAY, end: APRIL_1 + 9 * DAY }

    expect(visibleWindow(chosen, extent)).toEqual(chosen)
    expect(visibleWindow(null, extent)).toEqual(extent)
    expect(visibleWindow({ start: APRIL_1 - DAY, end: APRIL_1 + 5 * DAY }, extent)).toEqual(extent)
    expect(visibleWindow({ start: APRIL_1 + 5 * DAY, end: APRIL_1 + 5 * DAY }, extent)).toEqual(extent)
  })

  it('draws the rows in a window and one either side', () => {
    const shown = rowsInWindow(rows, { start: APRIL_1 + 4.5 * DAY, end: APRIL_1 + 8 * DAY })

    expect(shown.map(row => (row.time - APRIL_1) / DAY)).toEqual([4, 5, 6, 7, 8, 9])
    expect(rowsInWindow(rows, extent)).toHaveLength(20)
  })

  it('snaps a window outwards onto the days the rows have', () => {
    const gappy = dayRows([0, 3, 6, 9])

    expect(snapToRows({ start: APRIL_1 + 4 * DAY, end: APRIL_1 + 7.5 * DAY }, gappy)).toEqual({
      start: APRIL_1 + 3 * DAY,
      end: APRIL_1 + 9 * DAY
    })
    expect(snapToRows({ start: APRIL_1 - DAY, end: APRIL_1 + 20 * DAY }, gappy)).toEqual({
      start: APRIL_1,
      end: APRIL_1 + 9 * DAY
    })
  })

  it('widens a narrow window to a week around its middle, inside the rows', () => {
    const week = MIN_WINDOW_DAYS * DAY

    expect(widenWindow({ start: APRIL_1 + 10 * DAY, end: APRIL_1 + 10 * DAY }, extent)).toEqual({
      start: APRIL_1 + 10 * DAY - week / 2,
      end: APRIL_1 + 10 * DAY + week / 2
    })
    expect(widenWindow({ start: APRIL_1, end: APRIL_1 }, extent)).toEqual({ start: APRIL_1, end: APRIL_1 + week })
    expect(widenWindow({ start: extent.end, end: extent.end }, extent)).toEqual({
      start: extent.end - week,
      end: extent.end
    })
    const wide = { start: APRIL_1, end: APRIL_1 + 10 * DAY }
    expect(widenWindow(wide, extent)).toEqual(wide)
  })

  it('zooms in as far as a week', () => {
    expect(maxZoom({ start: APRIL_1, end: APRIL_1 + 70 * DAY })).toBe(10)
    expect(maxZoom({ start: APRIL_1, end: APRIL_1 + 3 * DAY })).toBe(1)
  })
})

describe('windowTicks', () => {
  it('labels a long window at the start of each month in it', () => {
    const ticks = windowTicks({ start: Date.UTC(2026, 3, 15), end: Date.UTC(2026, 9, 31) })

    expect(ticks.values.map(ticks.format)).toEqual(['May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct'])
  })

  it('labels a short window with days, spaced to keep the labels few', () => {
    const month = windowTicks({ start: Date.UTC(2026, 6, 1), end: Date.UTC(2026, 6, 31) })
    const week = windowTicks({ start: Date.UTC(2026, 6, 1), end: Date.UTC(2026, 6, 8) })

    expect(month.values.map(month.format)).toEqual(['Jul 1', 'Jul 8', 'Jul 15', 'Jul 22', 'Jul 29'])
    expect(week.values.map(week.format)).toEqual([
      'Jul 1',
      'Jul 2',
      'Jul 3',
      'Jul 4',
      'Jul 5',
      'Jul 6',
      'Jul 7',
      'Jul 8'
    ])
  })

  it('starts day labels at the first whole day in the window', () => {
    const ticks = windowTicks({ start: Date.UTC(2026, 6, 1, 6), end: Date.UTC(2026, 6, 5, 18) })

    expect(ticks.values[0]).toBe(Date.UTC(2026, 6, 2))
  })
})

describe('valueExtent', () => {
  it('spans the lowest to the highest value, the selected year included', () => {
    const rows = buildClimatologyRows(
      series({ observations: [{ date: '2026-04-01', value: 40, station_count: 1 }] }),
      2026,
      FULL_YEAR
    )

    expect(valueExtent(rows)).toEqual([2, 40])
  })
})

describe('formatRange', () => {
  it('has the unit once, and the decimals of the variable', () => {
    expect(formatRange(12.34, 20, 'temperature')).toBe('12.3 to 20.0°C')
    expect(formatRange(0, 4.2, 'wind_speed')).toBe('0.0 to 4.2 km/h')
    expect(formatRange(30.4, 55.6, 'relative_humidity')).toBe('30 to 56%')
  })
})

describe('latestRow', () => {
  const rows = dayRows([0, 1, 2, 3, 4]).map((row, index) => ({ ...row, value: index < 3 ? 20 : null }))
  const window = { start: rows[0].time, end: rows[4].time }

  it('is the last day with a value', () => {
    expect(latestRow(rows, window)).toBe(rows[2])
  })

  it('is inside the window', () => {
    expect(latestRow(rows, { start: rows[0].time, end: rows[1].time })).toBe(rows[1])
  })

  it('is the last day of the window when the year has no value in it', () => {
    expect(latestRow(rows, { start: rows[3].time, end: rows[4].time })).toBe(rows[4])
  })

  it('is null with no days in the window', () => {
    expect(latestRow([], window)).toBeNull()
  })
})
