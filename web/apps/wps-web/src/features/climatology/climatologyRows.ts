import type { ClimatologyVariable, DailyClimatology } from '@wps/api/climatologyAPI'

// One day on the chart: the historical distribution for that day of the year, and the selected
// year's value where there is one.
export interface ClimatologyRow {
  // UTC midnight of the day in the selected year, as milliseconds. A number so that the
  // chart's x scale is linear.
  time: number
  count: number
  minimum: number
  p25: number
  median: number
  p75: number
  p90: number
  maximum: number
  value: number | null
}

export interface ClimatologyVariableInfo {
  label: string
  unit: string
  decimals: number
}

export const CLIMATOLOGY_VARIABLES: Record<ClimatologyVariable, ClimatologyVariableInfo> = {
  temperature: { label: 'Temperature', unit: '°C', decimals: 1 },
  relative_humidity: { label: 'Relative humidity', unit: '%', decimals: 0 },
  wind_speed: { label: 'Wind speed', unit: 'km/h', decimals: 1 },
  precipitation: { label: '24 hour precipitation', unit: 'mm', decimals: 1 }
}

// Months are 1 to 12, and both ends are included.
export interface MonthRange {
  firstMonth: number
  lastMonth: number
}

export const FIRE_SEASON: MonthRange = { firstMonth: 4, lastMonth: 10 }
export const FULL_YEAR: MonthRange = { firstMonth: 1, lastMonth: 12 }

const utcDay = (year: number, month: number, day: number) => Date.UTC(year, month - 1, day)

/**
 * Lines up the historical days with the selected year's observations, one row per day of the
 * year that has history, within the months asked for. Rows are in calendar order.
 */
export const buildClimatologyRows = (climatology: DailyClimatology, range: MonthRange): ClimatologyRow[] => {
  const observed = new Map(climatology.observations.map(observation => [observation.date, observation.value]))
  return climatology.days
    .filter(day => day.month >= range.firstMonth && day.month <= range.lastMonth)
    .map(day => {
      const time = utcDay(climatology.year, day.month, day.day)
      return {
        time,
        count: day.count,
        minimum: day.minimum,
        p25: day.p25,
        median: day.median,
        p75: day.p75,
        p90: day.p90,
        maximum: day.maximum,
        value: observed.get(new Date(time).toISOString().slice(0, 10)) ?? null
      }
    })
}

/** The first day of each month in the range, as the times the x axis is labelled at. */
export const monthStarts = (year: number, range: MonthRange): number[] => {
  const starts: number[] = []
  for (let month = range.firstMonth; month <= range.lastMonth; month++) {
    starts.push(utcDay(year, month, 1))
  }
  return starts
}

const monthFormat = new Intl.DateTimeFormat('en-CA', { month: 'short', timeZone: 'UTC' })
const dayFormat = new Intl.DateTimeFormat('en-CA', { month: 'short', day: 'numeric', timeZone: 'UTC' })

export const formatMonth = (time: number) => monthFormat.format(time)
export const formatDay = (time: number) => dayFormat.format(time)

export const formatValue = (value: number, variable: ClimatologyVariable) => {
  const { unit, decimals } = CLIMATOLOGY_VARIABLES[variable]
  const separator = unit === '%' || unit === '°C' ? '' : ' '
  return `${value.toFixed(decimals)}${separator}${unit}`
}

/** Today as a time on the chart, if it is in the selected year and within the rows shown. */
export const todayOnChart = (rows: ClimatologyRow[], year: number, now: Date = new Date()): number | null => {
  if (rows.length === 0 || now.getFullYear() !== year) {
    return null
  }
  const today = utcDay(now.getFullYear(), now.getMonth() + 1, now.getDate())
  return today >= rows[0].time && today <= rows[rows.length - 1].time ? today : null
}
