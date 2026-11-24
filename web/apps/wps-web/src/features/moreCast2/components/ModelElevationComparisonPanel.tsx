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
import { isNull, isNumber } from 'lodash'
import { DateTime } from 'luxon'
import { type ChangeEvent, useState } from 'react'
import {
  calculateElevationAdjustmentInputs,
  type ElevationAdjustmentInput,
  formatElevationAdjustmentInput
} from '../elevationAdjustmentInputs'
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
  // state
  const [selectedModel, setSelectedModel] = useState('')
  // keep the entered value as text so clearing and typing do not lose the controlling field
  const [manualInput, setManualInput] = useState<ElevationAdjustmentInput | null>(null)
  const [message, setMessage] = useState('')
  const [overwriteExisting, setOverwriteExisting] = useState(false)

  // derived data
  const estimate =
    station && selectedModel
      ? estimatePreviousDayLapseRate(
          referenceWeather,
          station.stationCode,
          station.stationElevation,
          selectedModel,
          DateTime.now().setZone('America/Vancouver').minus({ days: 1 })
        )
      : { rate: null, explanation: 'Select a model to estimate a lapse rate.' }
  const effectiveInput = manualInput ?? { field: 'rate', value: estimate.rate?.toFixed(1) ?? '' }

  const modelElevation = station?.modelElevations[selectedModel as keyof typeof station.modelElevations]
  const hasElevations =
    isNumber(modelElevation) &&
    Number.isFinite(modelElevation) &&
    isNumber(station?.stationElevation) &&
    Number.isFinite(station.stationElevation)
  const differenceKm = hasElevations ? (modelElevation! - station!.stationElevation!) / 1000 : null
  const { rate, adjustment, canConvert } = calculateElevationAdjustmentInputs(effectiveInput, differenceKm)
  const displayValue = (field: ElevationAdjustmentInput['field'], value: number | null): string =>
    formatElevationAdjustmentInput(effectiveInput, field, value)
  const canApply = selectedModel !== '' && !isNull(adjustment) && Number.isFinite(adjustment)

  // callbacks
  const handleModelSelect = (model: string) => {
    if (model === selectedModel) return
    // carry manual rates across models, but calculate a new estimate after clearing
    if (effectiveInput.value.trim() === '') {
      setManualInput(null)
    } else if (manualInput && effectiveInput.field === 'adjustment') {
      setManualInput({ field: 'rate', value: !isNull(rate) && Number.isFinite(rate) ? rate.toFixed(1) : '' })
    }
    setSelectedModel(model)
    setMessage('')
  }

  const handleRateBlur = () => {
    if (manualInput && effectiveInput.field === 'rate' && !isNull(rate) && Number.isFinite(rate)) {
      setManualInput({ field: 'rate', value: rate.toFixed(1) })
    }
  }

  const handleRateChange = (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setManualInput({ field: 'rate', value: event.target.value })
    setMessage('')
  }

  const handleAdjustmentBlur = () => {
    if (effectiveInput.field === 'adjustment' && !isNull(adjustment) && Number.isFinite(adjustment)) {
      setManualInput({ field: 'adjustment', value: adjustment.toFixed(1) })
    }
  }

  const handleAdjustmentChange = (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setManualInput({ field: 'adjustment', value: event.target.value })
    setMessage('')
  }

  const handleOverwriteChange = (event: ChangeEvent<HTMLInputElement>) => {
    setOverwriteExisting(event.target.checked)
    setMessage('')
  }

  const handleApply = () => {
    if (!onApply || !canApply) return
    setMessage(onApply(selectedModel, adjustment!, overwriteExisting))
  }

  // render
  if (isNull(station)) return null

  return (
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
          {!isNull(station.stationElevation) && Number.isFinite(station.stationElevation) && (
            <Box component="span" sx={{ width: 24, borderBottom: '2px dashed', flexShrink: 0 }} />
          )}
          <Typography variant="body2">Station elevation: {formatElevation(station.stationElevation)}</Typography>
        </Box>
        <ElevationChart station={station} selected={selectedModel} onSelect={handleModelSelect} />
        {onApply && (
          <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Divider sx={{ mb: 1 }} />
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <Typography variant="subtitle2">Temperature adjustment</Typography>
              <Tooltip
                describeChild
                title={
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    <Typography component="div" variant="subtitle2">
                      Initial lapse rate
                    </Typography>
                    <Box component="p" sx={{ m: 0 }}>
                      Calculated using yesterday's observed noon temperature, the corresponding raw model temperature,
                      and the elevation difference between the model and station.
                    </Box>
                    <Box component="p" sx={{ m: 0 }}>
                      Not prefilled when the elevation difference is less than 100 m.
                    </Box>
                    <Box component="p" sx={{ m: 0 }}>
                      Automatic rates are limited to −9.8 to +9.8°C/km. You can enter either value manually without this
                      limit.
                    </Box>
                  </Box>
                }
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
                onBlur={handleRateBlur}
                onChange={handleRateChange}
              />

              <SyncAltIcon color="action" fontSize="small" />
              <TextField
                sx={{ flex: 1, minWidth: 0 }}
                slotProps={{ inputLabel: { shrink: true }, htmlInput: { step: 0.1 } }}
                size="small"
                label="Adjustment (°C)"
                type="number"
                value={displayValue('adjustment', adjustment)}
                onBlur={handleAdjustmentBlur}
                onChange={handleAdjustmentChange}
              />
            </Box>
            {!canConvert && (
              <Typography variant="caption">
                Lapse rate conversion requires different station and model elevations. You can enter an adjustment
                directly.
              </Typography>
            )}
            <FormControlLabel
              control={<Checkbox checked={overwriteExisting} onChange={handleOverwriteChange} />}
              label="Overwrite existing forecasts"
            />
            <Tooltip title="Fill temperature forecasts for this station in the selected date range." describeChild>
              <Box component="span" sx={{ display: 'block' }}>
                <Button fullWidth variant="contained" disabled={!canApply} onClick={handleApply}>
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
}

export default ModelElevationComparisonPanel
