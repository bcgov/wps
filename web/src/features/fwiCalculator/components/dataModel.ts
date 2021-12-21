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
    status: 'FORECAST',
    temp: Math.floor(Math.random() * 100) + 1,
    rh: Math.floor(Math.random() * 100) + 1,
    windDir: Math.floor(Math.random() * 100) + 1,
    windSpeed: Math.floor(Math.random() * 100) + 1,
    precip: Math.floor(Math.random() * 100) + 1,
    ffmc: Math.floor(Math.random() * 100) + 1,
    dmc: Math.floor(Math.random() * 100) + 1,
    dc: Math.floor(Math.random() * 100) + 1,
    isi: Math.floor(Math.random() * 100) + 1,
    bui: Math.floor(Math.random() * 100) + 1,
    fwi: Math.floor(Math.random() * 100) + 1
  }))
}
