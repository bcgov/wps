import { Box, Button, Typography } from '@mui/material'
import { useTheme } from '@mui/material/styles'
import { ChartsReferenceLine } from '@mui/x-charts/ChartsReferenceLine'
import { LineChart, type MarkElementProps } from '@mui/x-charts/LineChart'
import { WeatherDeterminate, weatherModelsWithTooltips } from '@wps/api/moreCast2API'
import { MORECAST_MODEL_COLORS } from '@wps/ui/theme'
import { formatElevation, type ModelElevationRow } from '../modelElevation'
import { ORDERED_COLUMN_HEADERS } from './ColumnDefBuilder'

type StationComparison = Pick<ModelElevationRow, 'stationName' | 'stationElevation' | 'modelElevations'>

const models = ORDERED_COLUMN_HEADERS.filter(
  model => weatherModelsWithTooltips.some(candidate => candidate === model) && model !== WeatherDeterminate.NAM
)
const elevationFormatter = new Intl.NumberFormat('en-CA', { maximumFractionDigits: 0, useGrouping: false })
const differenceFormatter = new Intl.NumberFormat('en-CA', {
  maximumFractionDigits: 0,
  useGrouping: false,
  signDisplay: 'exceptZero'
})
const yAxisWidth = 72
const margin = { left: 8, right: 8, top: 28, bottom: 8 }

const ElevationChart = ({
  station,
  selected,
  onSelect
}: {
  station: StationComparison
  selected: string
  onSelect: (model: string) => void
}) => {
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

  const elevations = stationElevation === null ? modelElevations : [...modelElevations, stationElevation]
  const minimum = elevations.length ? Math.min(...elevations) : 0
  const maximum = elevations.length ? Math.max(...elevations) : 0
  // leave room for labels and keep equal elevations on a useful scale
  const span = Math.max(maximum - minimum, 100) * 1.2
  const lowerBound = (minimum + maximum - span) / 2

  return (
    <>
      <Box sx={{ mt: 1 }}>
        {modelElevations.length === 0 && <Typography>Model elevations are not available for this station.</Typography>}
        <LineChart
          height={196}
          margin={margin}
          skipAnimation
          hideLegend
          grid={{ horizontal: true }}
          xAxis={[{ scaleType: 'band', data: models, position: 'none' }]}
          yAxis={[
            {
              min: lowerBound,
              max: lowerBound + span,
              width: yAxisWidth,
              label: 'Elevation (m)',
              tickNumber: 5,
              valueFormatter: (value: number) => elevationFormatter.format(value)
            }
          ]}
          series={points.map((point, index) => ({
            id: point.model,
            data: points.map((_, dataIndex) => (dataIndex === index ? point.elevation : null)),
            color: MORECAST_MODEL_COLORS[point.model.toLowerCase()].border,
            showMark: true,
            disableHighlight: true
          }))}
          slots={{
            tooltip: () => null,
            line: () => null,
            mark: (props: MarkElementProps) => {
              const point = points.find(point => point.model === props.seriesId)!
              return (
                <g data-model={point.model} aria-label={`${point.model} elevation ${formatElevation(point.elevation)}`}>
                  <circle
                    cx={props.x}
                    cy={props.y}
                    r={selected === point.model ? 7 : 5}
                    fill={props.color}
                    stroke={props.color}
                    strokeWidth={selected === point.model ? 3 : 0}
                  />
                  <text
                    x={props.x}
                    y={Number(props.y) - 12}
                    textAnchor="middle"
                    fill={theme.palette.text.primary}
                    fontSize={12}
                  >
                    {point.elevation === null ? 'N/A' : elevationFormatter.format(point.elevation)}
                  </text>
                </g>
              )
            }
          }}
          aria-label={`Model elevations compared with station elevation. Station: ${formatElevation(stationElevation)}. ${points.map(point => `${point.model}: ${formatElevation(point.elevation)}`).join('. ')}`}
        >
          {stationElevation !== null && (
            <g aria-label={`Station elevation ${formatElevation(stationElevation)}`}>
              <ChartsReferenceLine
                y={stationElevation}
                lineStyle={{ stroke: theme.palette.text.primary, strokeWidth: 2, strokeDasharray: '6 4' }}
              />
            </g>
          )}
        </LineChart>
      </Box>
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: `repeat(${models.length}, minmax(0, 1fr))`,
          ml: `${margin.left + yAxisWidth}px`,
          mr: `${margin.right}px`
        }}
      >
        {points.map(point => (
          <Box key={point.model} sx={{ minWidth: 0, px: 0.25, textAlign: 'center' }}>
            <Button
              size="small"
              fullWidth
              sx={{
                minWidth: 0,
                height: 28,
                px: 0,
                fontSize: 11,
                color: MORECAST_MODEL_COLORS[point.model.toLowerCase()].border,
                bgcolor: MORECAST_MODEL_COLORS[point.model.toLowerCase()].bg,
                borderColor: MORECAST_MODEL_COLORS[point.model.toLowerCase()].border,
                borderWidth: selected === point.model ? 2 : 1
              }}
              aria-pressed={selected === point.model}
              variant="outlined"
              onClick={() => onSelect(point.model)}
            >
              {point.model}
            </Button>
            <Typography
              variant="caption"
              component="div"
              sx={{ whiteSpace: 'nowrap' }}
              aria-label={
                point.difference === null
                  ? undefined
                  : `${point.model} elevation difference ${differenceFormatter.format(point.difference)} m`
              }
            >
              {point.elevation === null
                ? 'N/A'
                : point.difference === null
                  ? ''
                  : differenceFormatter.format(point.difference)}
            </Typography>
          </Box>
        ))}
      </Box>
      {stationElevation === null && (
        <Typography variant="caption" color="text.secondary">
          Station elevation unavailable. Differences cannot be calculated.
        </Typography>
      )}
    </>
  )
}

export default ElevationChart
