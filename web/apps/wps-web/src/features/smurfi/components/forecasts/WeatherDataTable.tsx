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

const cell: React.CSSProperties = {
  border: '1px solid black',
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

interface WeatherDataTableProps {
  rows: SpotForecastOutput['tabular_weather']
  issuedDate: string
}

const WeatherDataTable: React.FC<WeatherDataTableProps> = ({ rows, issuedDate }) => {
  const sorted = [...rows].sort((a, b) => a.forecast_time.localeCompare(b.forecast_time))

  return (
    <table role="presentation" style={{ borderCollapse: 'collapse', width: '100%', marginTop: 12 }}>
      <thead>
        <tr>
          <th style={{ ...hdrCell, textAlign: 'left' }}>Date/Time (PDT)</th>
          <th style={hdrCell}>Temp (C)</th>
          <th style={hdrCell}>RH</th>
          <th style={hdrCell}>Wind (km/h)</th>
          <th style={hdrCell}>Rain (mm)</th>
          <th style={hdrCell}>Chance Rain</th>
        </tr>
      </thead>
      <tbody>
        {sorted.map((row, i) => (
          <tr key={i}>
            <td style={cell}>{formatDateLabel(row.forecast_time, issuedDate)}</td>
            <td style={numCell}>{row.temperature ?? '-'}</td>
            <td style={numCell}>{row.relative_humidity ?? '-'}</td>
            <td style={numCell}>{row.wind ?? '-'}</td>
            <td style={dashCell}>{row.precipitation_amount ?? '-'}</td>
            <td style={dashCell}>{row.probability_of_precipitation ?? '-'}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

export default WeatherDataTable
