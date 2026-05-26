import React from 'react'
import { DateTime } from 'luxon'
import { SpotForecastOutput } from '@wps/api/SMURFIAPI'

const TIMEZONE = 'America/Vancouver'

const formatDateLabel = (dateTimeStr: string, issuedDateISO: string): string => {
  const dt = DateTime.fromISO(dateTimeStr).setZone(TIMEZONE)
  const issuedDay = DateTime.fromISO(issuedDateISO).setZone(TIMEZONE).startOf('day')
  const dayDiff = Math.round(dt.startOf('day').diff(issuedDay, 'days').days)
  const time = dt.toFormat('HHmm')

  if (dayDiff === 0) return `Today ${time}`
  if (dayDiff === 1) return dt.hour === 0 ? 'Tonight' : `Tomorrow ${time}`
  if (dayDiff === 2) return dt.hour === 0 ? 'Tomorrow night' : `Next Day ${time}`
  return dateTimeStr
}

const COLUMNS = '2fr 1fr 1fr 2fr 1fr 1fr'

const grid: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: COLUMNS,
  borderTop: '1px solid black',
  borderLeft: '1px solid black',
  marginTop: 12,
  width: '100%'
}

const cell: React.CSSProperties = {
  borderRight: '1px solid black',
  borderBottom: '1px solid black',
  padding: '3px 8px',
  verticalAlign: 'top',
  fontSize: '0.875rem'
}

const hdrCell: React.CSSProperties = {
  ...cell,
  fontWeight: 'bold',
  textAlign: 'center'
}

const numCell: React.CSSProperties = {
  ...cell,
  fontWeight: 'bold',
  textAlign: 'center'
}

const dashCell: React.CSSProperties = {
  ...cell,
  textAlign: 'center'
}

const HEADERS = ['Date/Time (PDT)', 'Temp (C)', 'RH', 'Wind (km/h)', 'Rain (mm)', 'Chance Rain']

interface WeatherDataTableProps {
  rows: SpotForecastOutput['tabular_weather']
  issuedDate: string
  fontSize?: string
}

const WeatherDataTable: React.FC<WeatherDataTableProps> = ({ rows, issuedDate, fontSize = '0.875rem' }) => {
  const sorted = [...rows].sort((a, b) => a.forecast_time.localeCompare(b.forecast_time))

  const cellWithSize: React.CSSProperties = { ...cell, fontSize }
  const numCellWithSize: React.CSSProperties = { ...numCell, fontSize }
  const dashCellWithSize: React.CSSProperties = { ...dashCell, fontSize }
  const hdrCellWithSize: React.CSSProperties = { ...hdrCell, fontSize }

  return (
    <div style={grid}>
      {HEADERS.map((header, i) => (
        <div key={header} style={i === 0 ? { ...hdrCellWithSize, textAlign: 'left' } : hdrCellWithSize}>
          {header}
        </div>
      ))}
      {sorted.map(row => (
        <React.Fragment key={row.forecast_time}>
          <div style={cellWithSize}>{formatDateLabel(row.forecast_time, issuedDate)}</div>
          <div style={numCellWithSize}>{row.temperature ?? '-'}</div>
          <div style={numCellWithSize}>{row.relative_humidity ?? '-'}</div>
          <div style={numCellWithSize}>{row.wind ?? '-'}</div>
          <div style={dashCellWithSize}>{row.precipitation_amount ?? '-'}</div>
          <div style={dashCellWithSize}>{row.probability_of_precipitation ?? '-'}</div>
        </React.Fragment>
      ))}
    </div>
  )
}

export default WeatherDataTable
