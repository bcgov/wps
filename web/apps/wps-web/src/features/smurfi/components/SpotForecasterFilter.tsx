import { Autocomplete, SxProps, TextField, Theme } from '@mui/material'
import { SpotRequestOutput } from '@wps/api/SMURFIAPI'
import { useMemo } from 'react'

interface SpotForecasterFilterProps {
  spotRequests: SpotRequestOutput[]
  value: string | null
  onChange: (forecasterName: string | null) => void
  label?: string
  sx?: SxProps<Theme>
}

const SpotForecasterFilter = ({
  spotRequests,
  value,
  onChange,
  label = 'Search by Forecaster',
  sx
}: SpotForecasterFilterProps) => {
  const forecasterOptions = useMemo(
    () =>
      [
        ...new Set(
          spotRequests
            .map(spot => spot.latest_forecast?.forecaster_name)
            .filter((name): name is string => Boolean(name))
        )
      ].sort((a, b) => a.localeCompare(b)),
    [spotRequests]
  )

  return (
    <Autocomplete
      size="small"
      sx={sx}
      options={forecasterOptions}
      value={value}
      onChange={(_, newValue) => onChange(newValue)}
      renderInput={params => <TextField {...params} label={label} variant="outlined" size="small" />}
    />
  )
}

export default SpotForecasterFilter
