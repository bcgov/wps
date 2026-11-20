import { Box, Typography } from '@mui/material'
import { formatElevation, type ModelElevationRow } from '../modelElevation'
import StationInfoTooltip from './StationInfoTooltip'

interface ModelElevationCellProps {
  row: ModelElevationRow
  field: string
  value: string
  hasFocus?: boolean
}

const ModelElevationCell = ({ row, field, value, hasFocus = false }: ModelElevationCellProps) => {
  if (field === 'stationName') {
    return (
      <Box
        component="span"
        sx={{
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          height: '100%',
          width: '100%',
          minWidth: 0
        }}
      >
        <Box component="span" sx={{ display: 'flex', alignItems: 'center', minWidth: 0 }}>
          <Typography component="span" variant="body2" noWrap sx={{ fontWeight: 600, lineHeight: '18px' }}>
            {row.stationName}
          </Typography>
          <StationInfoTooltip
            stationCode={row.stationCode}
            stationName={row.stationName}
            elevationLabel={formatElevation(row.stationElevation)}
            tabIndex={hasFocus ? 0 : -1}
          />
        </Box>
        <Typography component="span" variant="caption" sx={{ lineHeight: '16px' }}>
          Elevation: {formatElevation(row.stationElevation)}
        </Typography>
      </Box>
    )
  }
  return (
    <Typography
      component="span"
      variant="body2"
      noWrap
      sx={{
        fontWeight: 600,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: '100%',
        height: '100%',
        textAlign: 'center'
      }}
    >
      {value}
    </Typography>
  )
}

export default ModelElevationCell
