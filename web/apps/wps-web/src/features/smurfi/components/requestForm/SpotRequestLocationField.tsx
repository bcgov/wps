import React, { useEffect, useState } from 'react'
import { Box, FormHelperText, TextField, Typography } from '@mui/material'
import SpotRequestLocationMap from '@/features/smurfi/components/requestForm/SpotRequestLocationMap'
import { SpotRequestOutput } from '@wps/api/SMURFIAPI'

interface SpotRequestLocation {
  latitude: number
  longitude: number
}

interface SpotRequestLocationFieldProps {
  value: SpotRequestLocation | null
  onChange: (value: SpotRequestLocation | null) => void
  onBlur: () => void
  errorMessage?: string
  existingSpotRequests: SpotRequestOutput[]
}

const isValidCoordinate = (latitude: number, longitude: number) =>
  Number.isFinite(latitude) &&
  Number.isFinite(longitude) &&
  latitude >= -90 &&
  latitude <= 90 &&
  longitude >= -180 &&
  longitude <= 180

const SpotRequestLocationField: React.FC<SpotRequestLocationFieldProps> = ({
  value,
  onChange,
  onBlur,
  errorMessage,
  existingSpotRequests
}) => {
  const [latitudeInput, setLatitudeInput] = useState('')
  const [longitudeInput, setLongitudeInput] = useState('')

  useEffect(() => {
    if (value) {
      setLatitudeInput(value.latitude.toFixed(6))
      setLongitudeInput(value.longitude.toFixed(6))
    }
  }, [value])

  const updateLocationFromInputs = () => {
    if (!latitudeInput.trim() || !longitudeInput.trim()) {
      onChange(null)
      onBlur()
      return
    }

    const latitude = Number(latitudeInput)
    const longitude = Number(longitudeInput)

    if (isValidCoordinate(latitude, longitude)) {
      onChange({
        latitude: Number(latitude.toFixed(6)),
        longitude: Number(longitude.toFixed(6))
      })
      onBlur()
      return
    }

    onChange(null)
    onBlur()
  }

  const handleMapChange = (location: SpotRequestLocation | null) => {
    onChange(location)
    onBlur()
  }

  return (
    <Box>
      <Typography variant="subtitle1" sx={{ mb: 1 }}>
        Location
      </Typography>
      <Box sx={{ display: 'flex', gap: 2, mb: 1 }}>
        <TextField
          required
          label="Latitude"
          value={latitudeInput}
          onChange={event => setLatitudeInput(event.target.value)}
          onBlur={updateLocationFromInputs}
          error={!!errorMessage}
          size="small"
        />
        <TextField
          required
          label="Longitude"
          value={longitudeInput}
          onChange={event => setLongitudeInput(event.target.value)}
          onBlur={updateLocationFromInputs}
          error={!!errorMessage}
          size="small"
        />
      </Box>
      <SpotRequestLocationMap
        selectedLocation={value}
        onChange={handleMapChange}
        existingSpotRequests={existingSpotRequests}
      />
      {errorMessage && <FormHelperText error>{errorMessage}</FormHelperText>}
    </Box>
  )
}

export default SpotRequestLocationField
