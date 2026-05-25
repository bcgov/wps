import React from 'react'
import { Box, Typography } from '@mui/material'
import { DateTime } from 'luxon'
import { SpotForecastOutput, SpotRequestOutput } from '@wps/api/SMURFIAPI'
import { RepresentativeStation } from '@/features/smurfi/interfaces'

const TIMEZONE = 'America/Vancouver'

const toDDM = (decimal: number): string => {
  const abs = Math.abs(decimal)
  const degrees = Math.floor(abs)
  const minutes = ((abs - degrees) * 60).toFixed(3)
  return `${decimal < 0 ? '-' : ''}${degrees} ${minutes}`
}

const COLUMNS = '145px 210px 1fr 190px'

const grid: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: COLUMNS,
  borderTop: '1px solid black',
  borderLeft: '1px solid black',
  width: '100%'
}

const cell: React.CSSProperties = {
  borderRight: '1px solid black',
  borderBottom: '1px solid black',
  padding: '3px 8px',
  fontSize: '12px'
}

const span2: React.CSSProperties = {
  ...cell,
  gridColumn: 'span 2'
}

interface SpotForecastHeaderTableProps {
  forecast: SpotForecastOutput
  spotRequest: SpotRequestOutput
  representativeStations: RepresentativeStation[]
}

const SpotForecastHeaderTable: React.FC<SpotForecastHeaderTableProps> = ({ forecast, spotRequest, representativeStations }) => {
  const issuedDt = DateTime.fromISO(forecast.issued_at).setZone(TIMEZONE)
  const expiryDt = forecast.expires_at ? DateTime.fromISO(forecast.expires_at).setZone(TIMEZONE) : null

  const issuedStr = `${issuedDt.toFormat('HHmm')} ${issuedDt.offsetNameShort} ${issuedDt.toFormat('EEEE, MMMM d, yyyy')}`
  const expiryStr = expiryDt ? expiryDt.toFormat('EEEE MMMM d') : '—'

  const stationsStr =
    representativeStations.length > 0
      ? representativeStations.map(s => s.name + (s.elevation == null ? '' : ` (${s.elevation}m)`)).join(', ')
      : '—'
  const fireNumberStr = spotRequest.fire_number?.join(', ') ?? '—'

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
        <Typography variant="body2" sx={{ fontSize: '12px' }}>
          <strong style={{ textDecoration: 'underline' }}>Date/time Issued:</strong>
          {'  '}
          {issuedStr}
        </Typography>
        <Typography variant="body2" sx={{ fontSize: '12px' }}>
          <strong style={{ textDecoration: 'underline' }}>Default Expiry:</strong> {expiryStr}
        </Typography>
      </Box>

      <div style={grid}>
        <div style={{ ...cell, fontWeight: 'bold' }}>Fire/Proj #</div>
        <div style={cell}>{fireNumberStr}</div>
        <div style={span2}>
          Request by:{'  '}
          {spotRequest.requestor_name}
        </div>

        <div style={cell}>Forecast by</div>
        <div style={cell}>{forecast.forecaster_name}</div>
        <div style={cell}>Email: {forecast.forecaster_email}</div>
        <div style={cell}>Phone: {forecast.forecaster_phone ?? '—'}</div>

        <div style={cell}>Geographic</div>
        <div style={cell}>{spotRequest.geographic_description}</div>
        <div style={span2}>
          Representative <span style={{ textDecoration: 'underline' }}>Stations</span>: {stationsStr}
        </div>

        <div style={cell}>
          Coordinates (<span style={{ textDecoration: 'underline' }}>approx</span>)
        </div>
        <div style={cell}>
          {toDDM(spotRequest.latitude)},{toDDM(spotRequest.longitude)}
        </div>
        <div style={cell}>
          Slope/aspect:{'  '}
          {spotRequest.aspect ?? '—'}
        </div>
        <div style={cell} />

        <div style={cell}>Elevation</div>
        <div style={cell}>{spotRequest.elevation ? `${spotRequest.elevation} m` : '—'}</div>
        <div style={cell}>{forecast.fire_size ? `Size:   ${forecast.fire_size} ha` : ''}</div>
        <div style={cell} />
      </div>
    </Box>
  )
}

export default SpotForecastHeaderTable
