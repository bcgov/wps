import type { ClimatologyDay, DailyClimatology } from '@wps/api/climatologyAPI'
import {
  buildClimatologyRows,
  FIRE_SEASON,
  FULL_YEAR,
  formatDay,
  formatMonth,
  formatValue,
  monthStarts,
  todayOnChart
} from './climatologyRows'

const day = (month: number, dayOfMonth: number, median = 15): ClimatologyDay => ({
  month,
  day: dayOfMonth,
  count: 30,
  minimum: 2,
  p25: 10,
  median,
  p75: 20,
  p90: 25,
  maximum: 33
})

const climatology = (overrides: Partial<DailyClimatology> = {}): DailyClimatology => ({
  station_code: 322,
  variable: 'temperature',
  year: 2026,
  first_reference_year: 1990,
  last_reference_year: 2025,
  days: [day(3, 31), day(4, 1), day(7, 1, 22), day(10, 31), day(11, 1)],
  observations: [
    { date: '2026-04-01', value: 8.5 },
    { date: '2026-11-01', value: 3 }
  ],
  ...overrides
})

describe('buildClimatologyRows', () => {
  it('keeps the days in the months asked for, in order, dated in the selected year', () => {
    const rows = buildClimatologyRows(climatology(), FIRE_SEASON)

    expect(rows.map(row => new Date(row.time).toISOString().slice(0, 10))).toEqual([
      '2026-04-01',
      '2026-07-01',
      '2026-10-31'
    ])
  })

  it('carries the distribution and the observation of the same day', () => {
    const [first, second] = buildClimatologyRows(climatology(), FIRE_SEASON)

    expect(first).toMatchObject({ minimum: 2, p25: 10, median: 15, p75: 20, p90: 25, maximum: 33, count: 30 })
    expect(first.value).toBe(8.5)
    expect(second.median).toBe(22)
  })

  it('has no value on a day the selected year has not observed', () => {
    const rows = buildClimatologyRows(climatology(), FIRE_SEASON)

    expect(rows[1].value).toBeNull()
  })

  it('shows every month for the full year', () => {
    expect(buildClimatologyRows(climatology(), FULL_YEAR)).toHaveLength(5)
  })

  it('has no rows without history', () => {
    expect(buildClimatologyRows(climatology({ days: [] }), FULL_YEAR)).toEqual([])
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
})

describe('todayOnChart', () => {
  const rows = buildClimatologyRows(climatology(), FIRE_SEASON)

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
