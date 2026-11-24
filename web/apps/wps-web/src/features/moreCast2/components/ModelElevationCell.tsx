import TerrainIcon from '@mui/icons-material/Terrain'
import { Box, IconButton, Tooltip, Typography } from '@mui/material'
import { formatElevation, type ModelElevationRow } from '../modelElevation'
import StationInfoTooltip from './StationInfoTooltip'

interface ModelElevationCellProps {
  row: ModelElevationRow
  field: string
  value: string
  model?: string
  hasFocus?: boolean
  onCompareElevations?: (stationCode: number) => void
}

const ModelElevationCell = ({
  row,
  field,
  value,
  model,
  hasFocus = false,
  onCompareElevations
}: ModelElevationCellProps) => {
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
        <Box component="span" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Typography component="span" variant="caption" sx={{ lineHeight: '16px' }}>
            Elevation: {formatElevation(row.stationElevation)}
          </Typography>
          {onCompareElevations && (
            <Tooltip title="Forecast by elevation" describeChild>
              <IconButton
                size="small"
                aria-label={`Compare model elevations for ${row.stationName}`}
                tabIndex={hasFocus ? 0 : -1}
                sx={{ p: 0, width: 16, height: 16 }}
                onClick={event => {
                  event.stopPropagation()
                  onCompareElevations(row.stationCode)
                }}
                onDoubleClick={event => event.stopPropagation()}
                onKeyDown={event => {
                  // keep grid keyboard handling from stealing the comparison button action
                  if (event.key === 'Enter' || event.key === ' ') event.stopPropagation()
                }}
              >
                <TerrainIcon sx={{ fontSize: 16 }} />
              </IconButton>
            </Tooltip>
          )}
        </Box>
      </Box>
    )
  }

  const elevation = (
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

  return model ? (
    <Tooltip title={`${model} Elevation`} describeChild>
      {elevation}
    </Tooltip>
  ) : (
    elevation
  )
}

export default ModelElevationCell
