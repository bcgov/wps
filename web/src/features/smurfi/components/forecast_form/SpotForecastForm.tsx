import React, { useContext, useEffect, useState, useMemo } from 'react'
import { useForm, useFieldArray } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useDispatch } from 'react-redux'
import { Grid, Typography, Button, Box, Switch, FormControlLabel } from '@mui/material'
import { DateTime } from 'luxon'
import { fetchWxStations } from '@/features/stations/slices/stationsSlice'
import { getStations, StationSource } from '@/api/stationAPI'
import { AppDispatch } from '@/app/store'
import { UserContext } from '@/features/smurfi/contexts/UserContext'
import { createSchema, FormData } from '@/features/smurfi/schemas/spotForecastSchema'
import { getDefaultValues, defaultWeatherRows } from '@/features/smurfi/constants/spotForecastDefaults'
import { SpotForecastHistoryItem, SpotForecastStatus } from '@/features/smurfi/interfaces'
import SpotForecastHeader from '@/features/smurfi/components/forecast_form/SpotForecastHeader'
import SpotForecastSynopsis from '@/features/smurfi/components/forecast_form/SpotForecastSynopsis'
import WeatherDataTable from '@/features/smurfi/components/forecast_form/WeatherDataTable'
import SpotForecastSummaries from '@/features/smurfi/components/forecast_form/SpotForecastSummaries'
import SpotForecastSections from '@/features/smurfi/components/forecast_form/SpotForecastSections'
import ForecastHistoryList from '@/features/smurfi/components/forecast_form/ForecastHistoryList'

// Mock data for all forecasts (including current) - in production this would come from an API
const mockAllForecasts: SpotForecastHistoryItem[] = [
  // Current/most recent forecasts
  {
    id: 100,
    fire_id: 'V0800168',
    latitude: 49.6188,
    longitude: -125.0313,
    issued_date: DateTime.now().toMillis(),
    expiry_date: DateTime.now().plus({ days: 1 }).toMillis(),
    forecaster: 'Matt',
    synopsis: 'Current forecast: High pressure continues to dominate with warm and dry conditions expected.',
    status: SpotForecastStatus.ACTIVE
  },
  {
    id: 105,
    fire_id: 'G0700234',
    latitude: 53.9171,
    longitude: -122.7497,
    issued_date: DateTime.now().toMillis(),
    expiry_date: DateTime.now().plus({ days: 1 }).toMillis(),
    forecaster: 'Jessie',
    synopsis: 'Current forecast: Unstable conditions with potential for afternoon thunderstorms.',
    status: SpotForecastStatus.ACTIVE
  },
  // Historical forecasts for V0800168
  {
    id: 101,
    fire_id: 'V0800168',
    latitude: 49.6188,
    longitude: -125.0313,
    issued_date: DateTime.now().minus({ days: 1 }).toMillis(),
    expiry_date: DateTime.now().toMillis(),
    forecaster: 'Matt',
    synopsis: 'A ridge of high pressure will bring warm and dry conditions to the region.',
    status: SpotForecastStatus.ARCHIVED
  },
  {
    id: 102,
    fire_id: 'V0800168',
    latitude: 49.6188,
    longitude: -125.0313,
    issued_date: DateTime.now().minus({ days: 2 }).toMillis(),
    expiry_date: DateTime.now().minus({ days: 1 }).toMillis(),
    forecaster: 'Jessie',
    synopsis: 'An approaching cold front will bring cooler temperatures and increased humidity.',
    status: SpotForecastStatus.ARCHIVED
  },
  {
    id: 103,
    fire_id: 'V0800168',
    latitude: 49.6188,
    longitude: -125.0313,
    issued_date: DateTime.now().minus({ days: 3 }).toMillis(),
    expiry_date: DateTime.now().minus({ days: 2 }).toMillis(),
    forecaster: 'Brett',
    synopsis: 'Stable conditions expected with light winds and moderate temperatures.',
    status: SpotForecastStatus.ARCHIVED
  },
  // Historical forecasts for G0700234
  {
    id: 104,
    fire_id: 'G0700234',
    latitude: 53.9171,
    longitude: -122.7497,
    issued_date: DateTime.now().minus({ days: 1 }).toMillis(),
    expiry_date: DateTime.now().toMillis(),
    forecaster: 'Liz',
    synopsis: 'Thunderstorm activity possible in the afternoon with gusty winds.',
    status: SpotForecastStatus.ARCHIVED
  }
]

// Mock function to get full forecast data by ID - in production this would be an API call
const getMockForecastData = (
  forecastId: number,
  user: { name: string; email: string; phone: string }
): Partial<FormData> => {
  const forecast = mockAllForecasts.find(f => f.id === forecastId)
  if (!forecast) return getDefaultValues(user)

  // Return mock data based on the forecast ID
  const baseData = getDefaultValues(user)
  return {
    ...baseData,
    issuedDate: DateTime.fromMillis(forecast.issued_date),
    expiryDate: DateTime.fromMillis(forecast.expiry_date),
    fireProj: forecast.fire_id,
    forecastBy: forecast.forecaster,
    latitude: String(forecast.latitude),
    longitude: String(forecast.longitude),
    synopsis: forecast.synopsis,
    inversionVenting: `Inversion data for forecast ${forecastId}`,
    outlook: `Outlook for forecast ${forecastId}`,
    confidenceDiscussion: `Confidence discussion for forecast ${forecastId}`,
    weatherData: defaultWeatherRows.map((row, idx) => ({
      ...row,
      temp: String(15 + idx + (forecastId % 10)),
      rh: String(45 + idx * 2),
      windSpeed: String(10 + idx),
      windDirection: String((idx * 45) % 360)
    }))
  }
}

interface SpotForecastFormProps {
  readOnly?: boolean
  fireId?: string
  latitude?: number
  longitude?: number
}

const SpotForecastForm: React.FC<SpotForecastFormProps> = ({ readOnly = false, fireId, latitude, longitude }) => {
  const user = useContext(UserContext)
  const dispatch: AppDispatch = useDispatch()
  const [isMini, setIsMini] = useState(false)
  const [selectedForecastId, setSelectedForecastId] = useState<number | null>(null)
  const [isInitialized, setIsInitialized] = useState(false)

  // Filter and sort forecasts by fireId (most recent first)
  const allForecasts = useMemo(() => {
    if (!fireId) return []
    return mockAllForecasts.filter(f => f.fire_id === fireId).sort((a, b) => b.issued_date - a.issued_date)
  }, [fireId])

  const {
    control,
    handleSubmit,
    reset,
    formState: { errors, isValid }
  } = useForm<FormData>({
    resolver: zodResolver(createSchema(isMini)),
    defaultValues: getDefaultValues(user),
    mode: 'onBlur',
    reValidateMode: 'onChange'
  })

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'weatherData'
  })

  const onSubmit = (data: FormData) => {
    // For mini forecasts, exclude forecast summary data
    const dataToSubmit = { ...data }
    if (isMini) {
      delete dataToSubmit.afternoonForecast
      delete dataToSubmit.tonightForecast
      delete dataToSubmit.tomorrowForecast
    }

    console.log('Submitted Forecast:', {
      ...dataToSubmit,
      issuedDate: dataToSubmit.issuedDate.toISO(),
      expiryDate: dataToSubmit.expiryDate.toISO(),
      weatherData: dataToSubmit.weatherData.map(row => ({
        ...row,
        temp: row.temp ? Number(row.temp) : '-',
        rh: row.rh ? Number(row.rh) : '-'
      }))
    })

    alert('Forecast submitted! Check console for formatted data.')
  }

  const handleSelectForecast = (forecast: SpotForecastHistoryItem) => {
    setSelectedForecastId(forecast.id)
    const forecastData = getMockForecastData(forecast.id, user)
    reset(forecastData as FormData)
  }

  // Auto-select the most recent forecast when the component loads in readOnly mode
  useEffect(() => {
    if (readOnly && allForecasts.length > 0 && !isInitialized) {
      const mostRecentForecast = allForecasts[0]
      setSelectedForecastId(mostRecentForecast.id)
      const forecastData = getMockForecastData(mostRecentForecast.id, user)
      reset(forecastData as FormData)
      setIsInitialized(true)
    }
  }, [readOnly, allForecasts, isInitialized, user, reset])

  // Reset initialization when fireId changes
  useEffect(() => {
    setIsInitialized(false)
    setSelectedForecastId(null)
  }, [fireId])

  useEffect(() => {
    dispatch(fetchWxStations(getStations, StationSource.wildfire_one))
  }, [])

  return (
    <Box sx={{ p: 3, maxWidth: 1400, mx: 'auto' }}>
      <Typography variant="h4" gutterBottom>
        {readOnly ? 'Spot Forecast' : 'Spot Forecast Form'}
      </Typography>

      {!readOnly && (
        <Box sx={{ mb: 2 }}>
          <FormControlLabel
            control={<Switch checked={isMini} onChange={e => setIsMini(e.target.checked)} />}
            label="Mini Spot"
          />
        </Box>
      )}

      {/* Forecast History List - show at top in readOnly mode */}
      {readOnly && allForecasts.length > 0 && (
        <ForecastHistoryList
          forecasts={allForecasts}
          selectedId={selectedForecastId}
          onSelectForecast={handleSelectForecast}
        />
      )}

      <form onSubmit={handleSubmit(onSubmit)}>
        <Grid container spacing={3}>
          <SpotForecastHeader control={control} errors={errors} readOnly={readOnly} />
          <SpotForecastSynopsis control={control} errors={errors} readOnly={readOnly} />
          {!isMini && <SpotForecastSummaries control={control} readOnly={readOnly} />}
          <WeatherDataTable
            control={control}
            errors={errors}
            fields={fields}
            append={append}
            remove={remove}
            readOnly={readOnly}
          />
          <SpotForecastSections control={control} errors={errors} isMini={isMini} readOnly={readOnly} />

          {/* Submit */}
          {!readOnly && (
            <Grid item xs={12}>
              <Button type="submit" variant="contained" size="large" fullWidth disabled={!isValid}>
                Submit Spot Forecast
              </Button>
            </Grid>
          )}
        </Grid>
      </form>
    </Box>
  )
}

export default SpotForecastForm
