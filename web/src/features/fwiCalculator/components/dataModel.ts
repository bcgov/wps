import { MultiFWIOutput } from 'api/multiFWIAPI'
import { DECIMAL_PLACES } from 'features/hfiCalculator/constants'
import { DateTime } from 'luxon'
import { pstFormatter } from 'utils/date'

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
export const disabledColumns = [
  { columnName: 'date', editingEnabled: false },
  { columnName: 'status', editingEnabled: false },
  { columnName: 'temp', editingEnabled: false },
  { columnName: 'rh', editingEnabled: false },
  { columnName: 'windDir', editingEnabled: false },
  { columnName: 'windSpeed', editingEnabled: false },
  { columnName: 'precip', editingEnabled: false },
  { columnName: 'ffmc', editingEnabled: false },
  { columnName: 'dmc', editingEnabled: false },
  { columnName: 'dc', editingEnabled: false },
  { columnName: 'isi', editingEnabled: false },
  { columnName: 'bui', editingEnabled: false },
  { columnName: 'fwi', editingEnabled: false }
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

export const output2Rows = (multiFWIOutputs: MultiFWIOutput[]): MultiDayRow[] => {
  return multiFWIOutputs.map(output => ({
    id: output.id,
    date: DateTime.fromISO(pstFormatter(DateTime.fromISO(output.datetime))).toFormat(
      'yyyy/MMM/dd'
    ),
    status: output.status,
    temp: Number(output.temp?.toFixed(DECIMAL_PLACES)),
    rh: Number(output.rh?.toFixed(DECIMAL_PLACES)),
    windDir: Number(output.windDir?.toFixed(DECIMAL_PLACES)),
    windSpeed: Number(output.windSpeed?.toFixed(DECIMAL_PLACES)),
    precip: Number(output.precip?.toFixed(DECIMAL_PLACES)),
    ffmc: Number(output.actual.ffmc?.toFixed(DECIMAL_PLACES)),
    dmc: Number(output.actual.dmc?.toFixed(DECIMAL_PLACES)),
    dc: Number(output.actual.dc?.toFixed(DECIMAL_PLACES)),
    isi: Number(output.actual.isi?.toFixed(DECIMAL_PLACES)),
    bui: Number(output.actual.bui?.toFixed(DECIMAL_PLACES)),
    fwi: Number(output.actual.fwi?.toFixed(DECIMAL_PLACES))
  }))
}
