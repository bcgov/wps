import { DateTime } from 'luxon'

export interface MultiDayRow {
  id: number
  date: string
  status: string | null
  temp: number | null
  rh: number | null
  windDir: number | null
  windSpeed: number | null
  precip: number | null
}

export interface MultiDayColumn {
  name: string
  title: string
}

export const defaultColumns = [
  { name: 'date', title: 'Date' },
  { name: 'status', title: 'Status' },
  { name: 'temp', title: 'Temperature' },
  { name: 'rh', title: 'Relative Humidity' },
  { name: 'windDir', title: 'Wind Direction' },
  { name: 'windSpeed', title: 'Wind Speed' },
  { name: 'precip', title: 'Precipitation' },
  { name: 'ffmc', title: 'FFMC' },
  { name: 'dmc', title: 'DMC' },
  { name: 'dc', title: 'DC' },
  { name: 'isi', title: 'ISI' },
  { name: 'bui', title: 'BUI' },
  { name: 'fwi', title: 'FWI' }
]

export const generateDefaultRowsFromDates = (dates: DateTime[]): MultiDayRow[] => {
  return dates.map((date, idx) => ({
    id: idx,
    date: date.toFormat('yyyy/MMM/dd'),
    status: null,
    temp: null,
    rh: null,
    windDir: null,
    windSpeed: null,
    precip: null,
    ffmc: null,
    dmc: null,
    dc: null,
    isi: null,
    bui: null,
    fwi: null
  }))
}
