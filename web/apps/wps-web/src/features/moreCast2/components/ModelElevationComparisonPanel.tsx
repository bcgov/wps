import CloseIcon from '@mui/icons-material/Close'
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined'
import SyncAltIcon from '@mui/icons-material/SyncAlt'
import {
  Box,
  Button,
  Checkbox,
  Divider,
  FormControlLabel,
  IconButton,
  TextField,
  Tooltip,
  Typography
} from '@mui/material'
import { useTheme } from '@mui/material/styles'
import { WeatherDeterminate, weatherModelsWithTooltips } from '@wps/api/moreCast2API'
import { DateTime } from 'luxon'
import { useState } from 'react'
import { formatElevation, type ModelElevationRow } from '../modelElevation'
import { estimatePreviousDayLapseRate, type PreviousDayWeather } from '../previousDayLapseRate'
import { ORDERED_COLUMN_HEADERS } from './ColumnDefBuilder'

type StationComparison = Pick<ModelElevationRow, 'stationCode' | 'stationName' | 'stationElevation' | 'modelElevations'>

interface ModelElevationComparisonPanelProps {
  station: StationComparison | null
  referenceWeather: PreviousDayWeather
  onApply?: (model: string, adjustmentCelsius: number, overwriteExisting: boolean) => string
  onClose: () => void
}

const models = ORDERED_COLUMN_HEADERS.filter(
  model => weatherModelsWithTooltips.some(candidate => candidate === model) && model !== WeatherDeterminate.NAM
)
const differenceFormatter = new Intl.NumberFormat('en-CA', { maximumFractionDigits: 0, signDisplay: 'exceptZero' })
const tickFormatter = new Intl.NumberFormat('en-CA', { maximumFractionDigits: 0 })
const plot = { left: 48, right: 392, top: 36, bottom: 176 }

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
  const y = (elevation: number): number => plot.bottom - ((elevation - lowerBound) / span) * (plot.bottom - plot.top)
  const ticks = Array.from({ length: 5 }, (_, index) => lowerBound + (span * index) / 4)

  return (
    <>
      <Box sx={{ mt: 1 }}>
        {modelElevations.length === 0 && <Typography>Model elevations are not available for this station.</Typography>}
        <Box
          component="svg"
          viewBox="0 0 400 196"
          role="img"
          aria-labelledby="model-elevation-chart-title"
          aria-describedby="model-elevation-chart-description"
          sx={{ display: 'block', width: '100%', fontFamily: theme.typography.fontFamily, fontSize: 13 }}
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
                    <circle
                      cx={x}
                      cy={y(point.elevation)}
                      r={selected === point.model ? 8 : 5}
                      fill={theme.palette.primary.main}
                    />
                    <text x={x} y={y(point.elevation) - 10} fill={theme.palette.text.primary}>
                      {formatElevation(point.elevation)}
                    </text>
                  </>
                )}
              </g>
            )
          })}
        </Box>
      </Box>
      <Box sx={{ display: 'grid', gridTemplateColumns: `repeat(${models.length}, 1fr)`, ml: '12%', mr: '2%' }}>
        {points.map(point => (
          <Box key={point.model} sx={{ textAlign: 'center' }}>
            <Button
              size="small"
              sx={{ minWidth: 0, px: 0, fontSize: 11 }}
              aria-pressed={selected === point.model}
              variant={selected === point.model ? 'contained' : 'text'}
              onClick={() => onSelect(point.model)}
            >
              {point.model}
            </Button>
            <Typography variant="caption" component="div">
              {point.elevation === null
                ? 'N/A'
                : point.difference === null
                  ? ''
                  : `${differenceFormatter.format(point.difference)} m`}
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

const ModelElevationComparisonPanel = ({
  station,
  referenceWeather,
  onClose,
  onApply
}: ModelElevationComparisonPanelProps) => {
  const [selected, setSelected] = useState('')
  // keep the entered value as text so clearing and typing do not lose the controlling field
  const [manualInput, setInput] = useState<{ field: 'rate' | 'adjustment'; value: string } | null>(null)
  const estimate =
    station && selected
      ? estimatePreviousDayLapseRate(
          referenceWeather,
          station.stationCode,
          station.stationElevation,
          selected,
          DateTime.now().setZone('America/Vancouver').minus({ days: 1 })
        )
      : { rate: null, explanation: 'Select a model to estimate a lapse rate.' }
  const input = manualInput ?? { field: 'rate', value: estimate.rate?.toFixed(1) ?? '' }
  const [message, setMessage] = useState('')
  const [overwriteExisting, setOverwriteExisting] = useState(false)
  const modelElevation = station?.modelElevations[selected as keyof typeof station.modelElevations]
  const hasElevations =
    typeof modelElevation === 'number' &&
    Number.isFinite(modelElevation) &&
    typeof station?.stationElevation === 'number' &&
    Number.isFinite(station.stationElevation)
  const differenceKm = hasElevations ? (modelElevation! - station!.stationElevation!) / 1000 : null
  const canConvert = differenceKm !== null && differenceKm !== 0
  const entered =
    input.value.trim() !== '' && Number.isFinite(Number(input.value)) ? Number(Number(input.value).toFixed(1)) : null
  const unroundedRate =
    input.field === 'rate' ? entered : entered !== null && canConvert ? entered / differenceKm! : null
  const rate = unroundedRate !== null ? Number(unroundedRate.toFixed(1)) : null
  const unroundedAdjustment =
    input.field === 'adjustment' ? entered : rate !== null && differenceKm !== null ? rate * differenceKm : null
  const adjustment = unroundedAdjustment !== null ? Number(unroundedAdjustment.toFixed(1)) : null
  const displayValue = (field: 'rate' | 'adjustment', value: number | null): string =>
    input.field === field ? input.value : value !== null && Number.isFinite(value) ? value.toFixed(1) : ''
  const valid = selected !== '' && adjustment !== null && Number.isFinite(adjustment)
  return (
    station && (
      <Box
        component="section"
        aria-labelledby="model-elevation-comparison-title"
        sx={{
          display: 'flex',
          flexDirection: 'column',
          flexShrink: 0,
          minHeight: 0,
          position: 'absolute',
          inset: 0,
          border: 1,
          borderColor: 'divider',
          bgcolor: 'background.paper'
        }}
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            p: 1,
            flexShrink: 0,
            bgcolor: 'grey.100',
            borderBottom: 1,
            borderColor: 'divider'
          }}
        >
          <Typography
            id="model-elevation-comparison-title"
            variant="subtitle2"
            sx={{ flex: 1, minWidth: 0, fontWeight: 400, overflowWrap: 'anywhere' }}
          >
            Model elevations for{' '}
            <Box component="span" sx={{ fontWeight: 700 }}>
              {station.stationName}
            </Box>
          </Typography>
          <IconButton size="small" aria-label="Close elevation comparison" onClick={onClose}>
            <CloseIcon fontSize="small" />
          </IconButton>
        </Box>
        <Box sx={{ p: 1, flex: 1, overflowY: 'auto', minHeight: 0 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {station.stationElevation !== null && Number.isFinite(station.stationElevation) && (
              <Box component="span" sx={{ width: 24, borderBottom: '2px dashed', flexShrink: 0 }} />
            )}
            <Typography variant="body2">Station elevation: {formatElevation(station.stationElevation)}</Typography>
          </Box>
          <ElevationChart
            station={station}
            selected={selected}
            onSelect={model => {
              if (model === selected) return
              // carry manual rates across models, but calculate a new estimate after clearing
              if (input.value.trim() === '') {
                setInput(null)
              } else if (manualInput && input.field === 'adjustment') {
                setInput({ field: 'rate', value: rate !== null && Number.isFinite(rate) ? rate.toFixed(1) : '' })
              }
              setSelected(model)
              setMessage('')
            }}
          />
          {onApply && (
            <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Divider sx={{ mb: 1 }} />
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Typography variant="subtitle2">Temperature adjustment</Typography>
                <Tooltip
                  describeChild
                  title="Initially calculated using yesterday’s observed noon temperature, the corresponding raw model temperature, and the elevation difference between the model and station"
                >
                  <IconButton size="small" aria-label="How the lapse rate is prefilled">
                    <InfoOutlinedIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 1 }}>
                <TextField
                  sx={{ flex: 1, minWidth: 0 }}
                  slotProps={{ inputLabel: { shrink: true }, htmlInput: { step: 0.1 } }}
                  size="small"
                  label="Lapse rate (°C/km)"
                  type="number"
                  disabled={!canConvert}
                  value={displayValue('rate', rate)}
                  onBlur={() => {
                    if (manualInput && input.field === 'rate' && rate !== null && Number.isFinite(rate)) {
                      setInput({ field: 'rate', value: rate.toFixed(1) })
                    }
                  }}
                  onChange={event => {
                    setInput({ field: 'rate', value: event.target.value })
                    setMessage('')
                  }}
                />

                <SyncAltIcon color="action" fontSize="small" />
                <TextField
                  sx={{ flex: 1, minWidth: 0 }}
                  slotProps={{ inputLabel: { shrink: true }, htmlInput: { step: 0.1 } }}
                  size="small"
                  label="Adjustment (°C)"
                  type="number"
                  value={displayValue('adjustment', adjustment)}
                  onBlur={() => {
                    if (input.field === 'adjustment' && adjustment !== null && Number.isFinite(adjustment)) {
                      setInput({ field: 'adjustment', value: adjustment.toFixed(1) })
                    }
                  }}
                  onChange={event => {
                    setInput({ field: 'adjustment', value: event.target.value })
                    setMessage('')
                  }}
                />
              </Box>
              {!canConvert && (
                <Typography variant="caption">
                  Lapse rate conversion requires different station and model elevations. You can enter an adjustment
                  directly.
                </Typography>
              )}
              <FormControlLabel
                control={
                  <Checkbox
                    checked={overwriteExisting}
                    onChange={event => {
                      setOverwriteExisting(event.target.checked)
                      setMessage('')
                    }}
                  />
                }
                label="Overwrite existing forecasts"
              />
              <Tooltip title="Fill temperature forecasts for this station in the selected date range." describeChild>
                <Box component="span" sx={{ display: 'block' }}>
                  <Button
                    fullWidth
                    variant="contained"
                    disabled={!valid}
                    onClick={() => {
                      setMessage(onApply(selected, adjustment!, overwriteExisting))
                    }}
                  >
                    Fill temperature forecasts
                  </Button>
                </Box>
              </Tooltip>
              {message && (
                <Typography role="status" variant="body2">
                  {message}
                </Typography>
              )}
            </Box>
          )}
        </Box>
      </Box>
    )
  )
}

export default ModelElevationComparisonPanel
