import { Box, Button, Typography } from '@mui/material'
import { useTheme } from '@mui/material/styles'
import { ChartsReferenceLine } from '@mui/x-charts/ChartsReferenceLine'
import { LineChart, type MarkElementProps } from '@mui/x-charts/LineChart'
import type { MarkPropsOverrides } from '@mui/x-charts/models'
import { WeatherDeterminate, weatherModelsWithTooltips } from '@wps/api/moreCast2API'
import { MORECAST_MODEL_COLORS } from '@wps/ui/theme'
import { isNull, isNumber, isUndefined } from 'lodash'
import { formatElevation, type ModelElevationRow } from '../modelElevation'
import { ORDERED_COLUMN_HEADERS } from './ColumnDefBuilder'

// types
type StationComparison = Pick<ModelElevationRow, 'stationName' | 'stationElevation' | 'modelElevations'>

interface ElevationChartProps {
  station: StationComparison
  selected: string
  onSelect: (model: string) => void
}

interface ElevationPoint {
  model: string
  elevation: number | null
}

// mui needs this extension to accept our marker data through slotProps
declare module '@mui/x-charts/models' {
  interface MarkPropsOverrides {
    elevationPoints?: readonly ElevationPoint[]
    selectedModel?: string
  }
}

// configuration
const models = ORDERED_COLUMN_HEADERS.filter(
  model => (weatherModelsWithTooltips as readonly string[]).includes(model) && model !== WeatherDeterminate.NAM
)

const elevationFormatter = new Intl.NumberFormat('en-CA', { maximumFractionDigits: 0, useGrouping: false })
const differenceFormatter = new Intl.NumberFormat('en-CA', {
  maximumFractionDigits: 0,
  useGrouping: false,
  signDisplay: 'exceptZero'
})

const yAxisWidth = 72
const margin = { left: 8, right: 8, top: 28, bottom: 8 }

// label formatting
const getDifferenceLabel = (elevation: number | null, difference: number | null): string => {
  if (isNull(elevation)) return 'N/A'
  if (isNull(difference)) return ''

  return differenceFormatter.format(difference)
}

// marker rendering
const EmptyChartElement = () => null

const ElevationMark = (props: MarkElementProps & MarkPropsOverrides) => {
  const theme = useTheme()

  const point = props.elevationPoints?.find(point => point.model === props.seriesId)
  if (isUndefined(point) || isNull(point.elevation)) return null

  const isSelected = props.selectedModel === point.model

  return (
    <g data-model={point.model} aria-label={`${point.model} elevation ${formatElevation(point.elevation)}`}>
      <circle
        cx={props.x}
        cy={props.y}
        r={isSelected ? 7 : 5}
        fill={props.color}
        stroke={props.color}
        strokeWidth={isSelected ? 3 : 0}
      />
      <text x={props.x} y={Number(props.y) - 12} textAnchor="middle" fill={theme.palette.text.primary} fontSize={12}>
        {elevationFormatter.format(point.elevation)}
      </text>
    </g>
  )
}

const ElevationChart = ({ station, selected, onSelect }: ElevationChartProps) => {
  // derived data
  const theme = useTheme()
  const stationElevation =
    isNumber(station.stationElevation) && Number.isFinite(station.stationElevation) ? station.stationElevation : null

  const points = models.map(model => {
    const value = station.modelElevations[model]
    const elevation = isNumber(value) && Number.isFinite(value) ? value : null

    const difference = !isNull(elevation) && !isNull(stationElevation) ? elevation - stationElevation : null
    const differenceLabel = getDifferenceLabel(elevation, difference)
    const colors = MORECAST_MODEL_COLORS[model.toLowerCase()]

    return { model, elevation, difference, differenceLabel, colors }
  })

  const series = points.map((point, index) => ({
    id: point.model,
    data: points.map((_, dataIndex) => (dataIndex === index ? point.elevation : null)),
    color: point.colors.border,
    showMark: true,
    disableHighlight: true
  }))

  const modelDescription = points.map(point => `${point.model}: ${formatElevation(point.elevation)}`).join('. ')
  const modelElevations = points.flatMap(point => (isNull(point.elevation) ? [] : [point.elevation]))

  const elevations = isNull(stationElevation) ? modelElevations : [...modelElevations, stationElevation]
  const minimumElevation = elevations.length ? Math.min(...elevations) : 0
  const maximumElevation = elevations.length ? Math.max(...elevations) : 0

  // leave room for labels and keep equal elevations on a useful scale
  const elevationSpan = Math.max(maximumElevation - minimumElevation, 100) * 1.2
  const axisMinimum = (minimumElevation + maximumElevation - elevationSpan) / 2
  const axisMaximum = axisMinimum + elevationSpan

  // render
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
              min: axisMinimum,
              max: axisMaximum,
              width: yAxisWidth,
              label: 'Elevation (m)',
              tickNumber: 5,
              valueFormatter: (value: number) => elevationFormatter.format(value)
            }
          ]}
          series={series}
          slots={{ tooltip: EmptyChartElement, line: EmptyChartElement, mark: ElevationMark }}
          slotProps={{ mark: { elevationPoints: points, selectedModel: selected } }}
          aria-label={`Model elevations compared with station elevation. Station: ${formatElevation(stationElevation)}. ${modelDescription}`}
        >
          {!isNull(stationElevation) && (
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
                color: point.colors.border,
                bgcolor: point.colors.bg,
                borderColor: point.colors.border,
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
                isNull(point.difference)
                  ? undefined
                  : `${point.model} elevation difference ${differenceFormatter.format(point.difference)} m`
              }
            >
              {point.differenceLabel}
            </Typography>
          </Box>
        ))}
      </Box>
      {isNull(stationElevation) && (
        <Typography variant="caption" color="text.secondary">
          Station elevation unavailable. Differences cannot be calculated.
        </Typography>
      )}
    </>
  )
}

export default ElevationChart
