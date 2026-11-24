import type { ClimatologySeries, ClimatologyVariable } from '@wps/api/climatologyAPI'

// One day on the chart: the historical distribution for that day of the year, and the selected
// year's value where there is one.
export interface ClimatologyRow {
  // UTC midnight of the day in the selected year, as milliseconds. A number so that the
  // chart's x scale is linear.
  time: number
  count: number
  // How many stations the distribution is drawn from.
  stationCount: number
  minimum: number
  p25: number
  median: number
  p75: number
  p90: number
  maximum: number
  value: number | null
  // How many stations the value is the mean of, or null with no value.
  valueStationCount: number | null
  // The value in each compared year that has one for the day, by year.
  compared: Record<number, number>
}

export interface ClimatologyVariableInfo {
  label: string
  // Empty for an index, which has no unit.
  unit: string
  decimals: number
}

export const CLIMATOLOGY_VARIABLES: Record<ClimatologyVariable, ClimatologyVariableInfo> = {
  temperature: { label: 'Temperature', unit: '°C', decimals: 1 },
  relative_humidity: { label: 'Relative humidity', unit: '%', decimals: 0 },
  wind_speed: { label: 'Wind speed', unit: 'km/h', decimals: 1 },
  precipitation: { label: '24 hour precipitation', unit: 'mm', decimals: 1 },
  ffmc: { label: 'FFMC', unit: '', decimals: 1 },
  dmc: { label: 'DMC', unit: '', decimals: 1 },
  dc: { label: 'DC', unit: '', decimals: 0 },
  isi: { label: 'ISI', unit: '', decimals: 1 },
  bui: { label: 'BUI', unit: '', decimals: 1 },
  fwi: { label: 'FWI', unit: '', decimals: 1 }
}

/** The variable's name within a sentence: lower case, unless it is an acronym such as FFMC. */
export const variableInSentence = (variable: ClimatologyVariable) => {
  const { label } = CLIMATOLOGY_VARIABLES[variable]
  return label === label.toUpperCase() ? label : label.toLowerCase()
}

/** The variable's axis label, with its unit if it has one. */
export const axisLabel = (variable: ClimatologyVariable) => {
  const { label, unit } = CLIMATOLOGY_VARIABLES[variable]
  return unit ? `${label} (${unit})` : label
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
 * Lines up a series' historical days with its observations in `year` and the years it is compared
 * with, one row per day of the year that has history, within the months asked for. Rows are in
 * calendar order.
 */
export const buildClimatologyRows = (series: ClimatologySeries, year: number, range: MonthRange): ClimatologyRow[] => {
  const observed = new Map(series.observations.map(observation => [observation.date, observation]))
  const compared = series.compared_years.map(({ year: comparedYear, observations }) => ({
    year: comparedYear,
    // By month and day, such as 07-01, which is what the years have in common.
    byDay: new Map(observations.map(({ date, value }) => [date.slice(5), value]))
  }))
  return series.days
    .filter(day => day.month >= range.firstMonth && day.month <= range.lastMonth)
    .map(day => {
      const time = utcDay(year, day.month, day.day)
      const date = new Date(time).toISOString().slice(0, 10)
      const observation = observed.get(date)
      return {
        time,
        count: day.count,
        stationCount: day.station_count,
        minimum: day.minimum,
        p25: day.p25,
        median: day.median,
        p75: day.p75,
        p90: day.p90,
        maximum: day.maximum,
        value: observation?.value ?? null,
        valueStationCount: observation?.station_count ?? null,
        compared: Object.fromEntries(
          compared.flatMap(({ year: comparedYear, byDay }) => {
            const value = byDay.get(date.slice(5))
            return value === undefined ? [] : [[comparedYear, value]]
          })
        )
      }
    })
}

/** The lowest and highest value of any row, to give charts of several stations one y axis. */
export const valueExtent = (rows: ClimatologyRow[]): [number, number] => {
  const values = rows.flatMap(row =>
    row.value === null ? [row.minimum, row.maximum] : [row.minimum, row.maximum, row.value]
  )
  return [Math.min(...values), Math.max(...values)]
}

/** The first day of each month in the range, as the times the x axis is labelled at. */
export const monthStarts = (year: number, range: MonthRange): number[] => {
  const starts: number[] = []
  for (let month = range.firstMonth; month <= range.lastMonth; month++) {
    starts.push(utcDay(year, month, 1))
  }
  return starts
}

const DAY = 24 * 60 * 60 * 1000

// The dates the chart shows, as times on its x axis. Both ends are included.
export interface DateWindow {
  start: number
  end: number
}

// The narrowest window the chart zooms to.
export const MIN_WINDOW_DAYS = 7

/** The first to last day of the rows, or null with no rows. */
export const rowsExtent = (rows: ClimatologyRow[]): DateWindow | null =>
  rows.length === 0 ? null : { start: rows[0].time, end: rows[rows.length - 1].time }

/**
 * The window to show: the one chosen, if it is still inside the rows' extent, else the whole
 * extent. A window chosen for other rows, such as another year, falls back to the whole extent.
 */
export const visibleWindow = (chosen: DateWindow | null, extent: DateWindow): DateWindow =>
  chosen !== null && chosen.start >= extent.start && chosen.end <= extent.end && chosen.end > chosen.start
    ? chosen
    : extent

/**
 * The rows to draw for a window: those inside it, and the nearest row either side so that the
 * lines and bands run to the edges of the plot rather than stopping short of them.
 */
export const rowsInWindow = (rows: ClimatologyRow[], window: DateWindow): ClimatologyRow[] => {
  const first = Math.max(0, rows.findIndex(row => row.time >= window.start) - 1)
  const after = rows.findIndex(row => row.time > window.end)
  return rows.slice(first, after === -1 ? rows.length : after + 1)
}

/**
 * A window moved onto days the rows have: the start back to the nearest earlier day and the end
 * forward to the nearest later one. The timeline's handles can only rest on those days.
 */
export const snapToRows = (window: DateWindow, rows: ClimatologyRow[]): DateWindow => {
  const times = rows.map(row => row.time)
  const start = times.filter(time => time <= window.start).pop() ?? times[0]
  const end = times.find(time => time >= window.end) ?? times[times.length - 1]
  return { start, end }
}

/**
 * A window at least `MIN_WINDOW_DAYS` wide, kept inside the extent. A click on the timeline
 * without a drag proposes a window of one day, which this widens around that day.
 */
export const widenWindow = (window: DateWindow, extent: DateWindow): DateWindow => {
  const minimum = MIN_WINDOW_DAYS * DAY
  if (window.end - window.start >= minimum) {
    return window
  }
  if (extent.end - extent.start <= minimum) {
    return extent
  }
  const middle = (window.start + window.end) / 2
  const start = Math.min(Math.max(middle - minimum / 2, extent.start), extent.end - minimum)
  return { start, end: start + minimum }
}

/** How far the chart can zoom in on the extent, as a factor of its full width. */
export const maxZoom = (extent: DateWindow): number =>
  Math.max(1, (extent.end - extent.start) / (MIN_WINDOW_DAYS * DAY))

// The steps, in days, that day ticks are spaced at as the window narrows.
const DAY_TICK_STEPS = [1, 2, 7, 14]
const MAX_DAY_TICKS = 10
// Below this many days, months are too few to label the axis with, so days are used.
const DAY_TICKS_BELOW_DAYS = 75

export interface WindowTicks {
  values: number[]
  format: (time: number) => string
}

/** The times to label the x axis of a window at: month starts for a long window, else days. */
export const windowTicks = (window: DateWindow): WindowTicks => {
  const days = (window.end - window.start) / DAY
  const firstDay = Math.ceil(window.start / DAY) * DAY
  if (days >= DAY_TICKS_BELOW_DAYS) {
    const values: number[] = []
    const first = new Date(firstDay)
    for (let month = new Date(Date.UTC(first.getUTCFullYear(), first.getUTCMonth(), 1)); ; ) {
      const time = month.getTime()
      if (time > window.end) {
        break
      }
      if (time >= window.start) {
        values.push(time)
      }
      month = new Date(Date.UTC(month.getUTCFullYear(), month.getUTCMonth() + 1, 1))
    }
    return { values, format: formatMonth }
  }
  const step = DAY_TICK_STEPS.find(each => days / each <= MAX_DAY_TICKS) ?? DAY_TICK_STEPS[DAY_TICK_STEPS.length - 1]
  const values: number[] = []
  for (let time = firstDay; time <= window.end; time += step * DAY) {
    values.push(time)
  }
  return { values, format: formatDay }
}

const monthFormat = new Intl.DateTimeFormat('en-CA', { month: 'short', timeZone: 'UTC' })
const dayFormat = new Intl.DateTimeFormat('en-CA', { month: 'short', day: 'numeric', timeZone: 'UTC' })

export const formatMonth = (time: number) => monthFormat.format(time)
export const formatDay = (time: number) => dayFormat.format(time)

export const formatValue = (value: number, variable: ClimatologyVariable) => {
  const { unit, decimals } = CLIMATOLOGY_VARIABLES[variable]
  const separator = unit === '' || unit === '%' || unit === '°C' ? '' : ' '
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
