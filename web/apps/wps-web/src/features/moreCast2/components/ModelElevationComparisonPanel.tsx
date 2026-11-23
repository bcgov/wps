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
import { DateTime } from 'luxon'
import { useState } from 'react'
import { formatElevation, type ModelElevationRow } from '../modelElevation'
import { estimatePreviousDayLapseRate, type PreviousDayWeather } from '../previousDayLapseRate'
import ElevationChart from './ElevationChart'

type StationComparison = Pick<ModelElevationRow, 'stationCode' | 'stationName' | 'stationElevation' | 'modelElevations'>

interface ModelElevationComparisonPanelProps {
  station: StationComparison | null
  referenceWeather: PreviousDayWeather
  onApply?: (model: string, adjustmentCelsius: number, overwriteExisting: boolean) => string
  onClose: () => void
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
