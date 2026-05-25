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

const cell: React.CSSProperties = {
  border: '1px solid black',
  padding: '3px 8px',
  verticalAlign: 'top',
  fontSize: '0.875rem'
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

  const stationsStr = representativeStations.length > 0
    ? representativeStations.map(s => `${s.name}${s.elevation != null ? ` (${s.elevation}m)` : ''}`).join(', ')
    : '—'
  const fireNumberStr = spotRequest.fire_number?.join(', ') ?? '—'

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
        <Typography variant="body2">
          <strong style={{ textDecoration: 'underline' }}>Date/time Issued:</strong>
          {'  '}
          {issuedStr}
        </Typography>
        <Typography variant="body2">
          <strong style={{ textDecoration: 'underline' }}>Default Expiry:</strong> {expiryStr}
        </Typography>
      </Box>

      <table role="presentation" style={{ borderCollapse: 'collapse', width: '100%' }}>
        <colgroup>
          <col style={{ width: '145px' }} />
          <col style={{ width: '210px' }} />
          <col />
          <col style={{ width: '190px' }} />
        </colgroup>
        <tbody>
          <tr>
            <td style={{ ...cell, fontWeight: 'bold' }}>Fire/Proj #</td>
            <td style={cell}>{fireNumberStr}</td>
            <td colSpan={2} style={cell}>
              Request by:{'  '}
              {spotRequest.requestor_name}
            </td>
          </tr>
          <tr>
            <td style={cell}>Forecast by</td>
            <td style={cell}>{forecast.forecaster_name}</td>
            <td style={cell}>Email: {forecast.forecaster_email}</td>
            <td style={cell}>Phone: {forecast.forecaster_phone ?? '—'}</td>
          </tr>
          <tr>
            <td style={cell}>Geographic</td>
            <td style={cell}>{spotRequest.geographic_description}</td>
            <td colSpan={2} style={cell}>
              Representative <span style={{ textDecoration: 'underline' }}>Stns</span>: {stationsStr}
            </td>
          </tr>
          <tr>
            <td style={cell}>
              Coordinates (<span style={{ textDecoration: 'underline' }}>approx</span>)
            </td>
            <td style={cell}>
              {toDDM(spotRequest.latitude)},{toDDM(spotRequest.longitude)}
            </td>
            <td style={cell}>
              Slope/aspect:{'  '}
              {spotRequest.aspect ?? '—'}
            </td>
            <td style={cell} />
          </tr>
          <tr>
            <td style={cell}>Elevation</td>
            <td style={cell}>{spotRequest.elevation ? `${spotRequest.elevation} m` : '—'}</td>
            <td style={cell}>{forecast.fire_size ? `Size:   ${forecast.fire_size} ha` : ''}</td>
            <td style={cell} />
          </tr>
        </tbody>
      </table>
    </Box>
  )
}

export default SpotForecastHeaderTable
