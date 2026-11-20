import { Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, Typography } from '@mui/material'
import { useTheme } from '@mui/material/styles'
import { WeatherDeterminate, weatherModelsWithTooltips } from '@wps/api/moreCast2API'
import { formatElevation, type ModelElevationRow } from '../modelElevation'
import { ORDERED_COLUMN_HEADERS } from './ColumnDefBuilder'

interface ModelElevationComparisonDialogProps {
  station: ModelElevationRow | null
  onClose: () => void
}

const models = ORDERED_COLUMN_HEADERS.filter(
  model => weatherModelsWithTooltips.some(candidate => candidate === model) && model !== WeatherDeterminate.NAM
)
const differenceFormatter = new Intl.NumberFormat('en-CA', { maximumFractionDigits: 0, signDisplay: 'exceptZero' })
const tickFormatter = new Intl.NumberFormat('en-CA', { maximumFractionDigits: 0 })
const plot = { left: 64, right: 540, top: 40, bottom: 230 }

const ElevationChart = ({ station }: { station: ModelElevationRow }) => {
  const theme = useTheme()
  const stationElevation =
    typeof station.stationElevation === 'number' && Number.isFinite(station.stationElevation)
      ? station.stationElevation
      : null
  const points = models.map(model => {
    const value = station.modelElevations[model]
    const elevation = typeof value === 'number' && Number.isFinite(value) ? value : null
    const difference = elevation !== null && stationElevation !== null ? elevation - stationElevation : null
    return { model, elevation, difference }
  })
  const modelElevations = points.flatMap(point => (point.elevation === null ? [] : [point.elevation]))
  if (modelElevations.length === 0) {
    return <Typography sx={{ my: 3 }}>Model elevations are not available for this station.</Typography>
  }

  const elevations = stationElevation === null ? modelElevations : [...modelElevations, stationElevation]
  const minimum = Math.min(...elevations)
  const maximum = Math.max(...elevations)
  // leave room for labels and keep equal elevations on a useful scale
  const span = Math.max(maximum - minimum, 100) * 1.2
  const lowerBound = (minimum + maximum - span) / 2
  const y = (elevation: number): number => plot.bottom - ((elevation - lowerBound) / span) * (plot.bottom - plot.top)
  const ticks = Array.from({ length: 5 }, (_, index) => lowerBound + (span * index) / 4)

  return (
    <>
      <Box sx={{ overflowX: 'auto', mt: 2 }}>
        <Box
          component="svg"
          viewBox="0 0 560 315"
          role="img"
          aria-labelledby="model-elevation-chart-title"
          aria-describedby="model-elevation-chart-description"
          sx={{ display: 'block', width: '100%', minWidth: 420, fontFamily: theme.typography.fontFamily, fontSize: 13 }}
        >
          <title id="model-elevation-chart-title">Model elevations compared with station elevation</title>
          <desc id="model-elevation-chart-description">
            Station elevation: {formatElevation(stationElevation)}.{' '}
            {points
              .map(
                point =>
                  `${point.model}: ${formatElevation(point.elevation)}${point.difference === null ? '' : `, ${differenceFormatter.format(point.difference)} m difference from station`}`
              )
              .join('. ')}
          </desc>
          <text x={0} y={16} fill={theme.palette.text.secondary}>
            Elevation (m)
          </text>
          {ticks.map(tick => (
            <g key={tick}>
              <line x1={plot.left} x2={plot.right} y1={y(tick)} y2={y(tick)} stroke={theme.palette.divider} />
              <text x={plot.left - 10} y={y(tick) + 4} textAnchor="end" fill={theme.palette.text.secondary}>
                {tickFormatter.format(tick)}
              </text>
            </g>
          ))}
          {stationElevation !== null && (
            <line
              x1={plot.left}
              x2={plot.right}
              y1={y(stationElevation)}
              y2={y(stationElevation)}
              stroke={theme.palette.text.primary}
              strokeWidth={2}
              strokeDasharray="6 4"
              aria-label={`Station elevation ${formatElevation(stationElevation)}`}
            />
          )}
          {points.map((point, index) => {
            const x = plot.left + ((index + 0.5) * (plot.right - plot.left)) / points.length
            return (
              <g key={point.model} data-model={point.model} textAnchor="middle">
                {point.elevation !== null && (
                  <>
                    <circle cx={x} cy={y(point.elevation)} r={5} fill={theme.palette.primary.main} />
                    <text x={x} y={y(point.elevation) - 12} fill={theme.palette.text.primary}>
                      {formatElevation(point.elevation)}
                    </text>
                  </>
                )}
                <text x={x} y={263} fill={theme.palette.text.primary} fontWeight={600}>
                  {point.model}
                </text>
                <text x={x} y={286} fill={theme.palette.text.secondary}>
                  {point.elevation === null
                    ? 'N/A'
                    : point.difference === null
                      ? ''
                      : `${differenceFormatter.format(point.difference)} m`}
                </text>
              </g>
            )
          })}
        </Box>
      </Box>
      <Typography variant="caption" color="text.secondary">
        {stationElevation === null
          ? 'Station elevation unavailable. Differences cannot be calculated.'
          : 'Differences from station elevation are shown below each model.'}
      </Typography>
    </>
  )
}

const ModelElevationComparisonDialog = ({ station, onClose }: ModelElevationComparisonDialogProps) => (
  <Dialog
    open={station !== null}
    onClose={onClose}
    fullWidth
    maxWidth="sm"
    aria-labelledby="model-elevation-comparison-title"
  >
    <DialogTitle id="model-elevation-comparison-title">Model elevations for {station?.stationName}</DialogTitle>
    {station && (
      <DialogContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {station.stationElevation !== null && Number.isFinite(station.stationElevation) && (
            <Box component="span" sx={{ width: 24, borderBottom: '2px dashed', flexShrink: 0 }} />
          )}
          <Typography variant="body2">Station elevation: {formatElevation(station.stationElevation)}</Typography>
        </Box>
        <ElevationChart station={station} />
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          Uses the model runs shown in the grid headers.
        </Typography>
      </DialogContent>
    )}
    <DialogActions>
      <Button onClick={onClose}>Close</Button>
    </DialogActions>
  </Dialog>
)

export default ModelElevationComparisonDialog
