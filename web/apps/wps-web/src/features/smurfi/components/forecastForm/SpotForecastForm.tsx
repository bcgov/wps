import React, { useCallback, useEffect, useState, useMemo } from 'react'
import { useForm, useFieldArray } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useDispatch, useSelector } from 'react-redux'
import { Alert, Grid, Typography, Button, Box, Switch, FormControlLabel } from '@mui/material'
import { DateTime } from 'luxon'
import { fetchWxStations } from '@/features/stations/slices/stationsSlice'
import { AppDispatch } from '@/app/store'
import { RootState } from '@/app/rootReducer'
import { getDefaultValues, defaultWeatherRows } from '@/features/smurfi/constants/spotForecastDefaults'
import SpotForecastHeader from '@/features/smurfi/components/forecastForm/SpotForecastHeader'
import SpotForecastSynopsis from '@/features/smurfi/components/forecastForm/SpotForecastSynopsis'
import WeatherDataTable from '@/features/smurfi/components/forecastForm/WeatherDataTable'
import SpotForecastSummaries from '@/features/smurfi/components/forecastForm/SpotForecastSummaries'
import SpotForecastSections from '@/features/smurfi/components/forecastForm/SpotForecastSections'
import { SpotForecastOutput, SpotRequestOutput } from '@wps/api/SMURFIAPI'
import { createSchema, SpotFormData } from '@wps/api/schema/spotForecastSchema'
import { getStations, StationSource } from '@wps/api/stationAPI'
import {
  clearSpotForecastSubmitState,
  fetchSpotForecasts,
  submitSpotForecast
} from '@/features/smurfi/slices/smurfiSlice'

const FORECAST_TIME_FORMAT = 'yyyy-MM-dd HH:mm'

const toLocalDateTime = (dateTime: string | undefined) => {
  if (!dateTime) {
    return undefined
  }
  const parsedDateTime = DateTime.fromISO(dateTime).setZone('America/Vancouver')
  return parsedDateTime.isValid ? parsedDateTime : undefined
}

const toDateTimeField = (dateTime: string) => toLocalDateTime(dateTime)?.toFormat(FORECAST_TIME_FORMAT) ?? dateTime

const toFormNumber = (value: number | null | undefined) => value ?? undefined

const toFormString = (value: number | string | null | undefined) =>
  value === null || value === undefined ? '' : String(value)

const getDescriptiveWeather = (forecast: SpotForecastOutput, period: 'Today' | 'Tonight' | 'Tomorrow') =>
  forecast.descriptive_weather.find(weather => weather.period === period)

interface SpotForecastFormProps {
  fireId?: string
  latitude?: number
  longitude?: number
  spotRequestId?: number
  spotRequest?: SpotRequestOutput
  fireCentreName?: string
}

const SpotForecastForm: React.FC<SpotForecastFormProps> = ({
  fireId,
  latitude,
  longitude,
  spotRequestId,
  spotRequest,
  fireCentreName
}) => {
  const dispatch: AppDispatch = useDispatch()
  const {
    spotForecastSubmitting,
    spotForecastSubmitError,
    spotForecastsByRequestId,
    spotForecastsError,
    spotForecastsLoading
  } = useSelector((state: RootState) => state.smurfi)
  const [isMini, setIsMini] = useState(false)
  const [selectedSpotForecast, setSelectedSpotForecast] = useState<SpotForecastOutput | undefined>(undefined)
  const [isInitialized, setIsInitialized] = useState(false)
  const schema = useMemo(() => createSchema(isMini), [isMini])
  const resolver = useMemo(() => zodResolver(schema), [schema])
  const effectiveSpotRequestId = spotRequestId ?? spotRequest?.id
  const spotForecasts = effectiveSpotRequestId ? (spotForecastsByRequestId[effectiveSpotRequestId] ?? []) : []

  const requestDefaultValues = useMemo<Partial<SpotFormData>>(() => {
    const defaultValues = getDefaultValues()
    const requestStart = toLocalDateTime(spotRequest?.start_at)
    const requestEnd = toLocalDateTime(spotRequest?.end_at)
    const requestFireId = spotRequest?.fire_number?.[0] ?? fireId ?? ''
    const requestLatitude = spotRequest?.latitude ?? latitude
    const requestLongitude = spotRequest?.longitude ?? longitude

    return {
      ...defaultValues,
      issuedDate: requestStart ?? defaultValues.issuedDate,
      expiryDate: requestEnd ?? defaultValues.expiryDate,
      fireProj: requestFireId,
      requestBy: spotRequest?.requestor_name ?? defaultValues.requestBy,
      latitude: toFormString(requestLatitude),
      longitude: toFormString(requestLongitude),
      slopeAspect: spotRequest?.aspect ?? defaultValues.slopeAspect,
      elevation: toFormString(spotRequest?.elevation),
      weatherData: defaultWeatherRows
    }
  }, [fireCentreName, fireId, latitude, longitude, spotRequest])

  const getForecastFormData = useCallback(
    (forecast: SpotForecastOutput): Partial<SpotFormData> => {
      const today = getDescriptiveWeather(forecast, 'Today')
      const tonight = getDescriptiveWeather(forecast, 'Tonight')
      const tomorrow = getDescriptiveWeather(forecast, 'Tomorrow')

      return {
        ...requestDefaultValues,
        issuedDate: toLocalDateTime(forecast.for_date) ?? requestDefaultValues.issuedDate,
        stns: forecast.representative_station_codes ?? [],
        size: toFormString(forecast.fire_size),
        synopsis: forecast.synopsis ?? '',
        afternoonForecast: {
          description: today?.conditions ?? '',
          maxTemp: toFormNumber(today?.temperature),
          minRh: toFormNumber(today?.relative_humidity)
        },
        tonightForecast: {
          description: tonight?.conditions ?? '',
          minTemp: toFormNumber(tonight?.temperature),
          maxRh: toFormNumber(tonight?.relative_humidity)
        },
        tomorrowForecast: {
          description: tomorrow?.conditions ?? '',
          maxTemp: toFormNumber(tomorrow?.temperature),
          minRh: toFormNumber(tomorrow?.relative_humidity)
        },
        weatherData:
          forecast.tabular_weather.length > 0
            ? forecast.tabular_weather.map(row => ({
                id: row.id,
                dateTime: toDateTimeField(row.forecast_time),
                temp: toFormString(row.temperature),
                rh: toFormString(row.relative_humidity),
                wind: row.wind ?? '',
                rain: toFormString(row.precipitation_amount),
                chanceRain: toFormString(row.probability_of_precipitation)
              }))
            : defaultWeatherRows,
        inversionVenting: forecast.inversion_and_venting ?? '',
        outlook: forecast.outlook ?? '',
        confidenceDiscussion: forecast.confidence ?? ''
      }
    },
    [requestDefaultValues]
  )

  const {
    control,
    handleSubmit,
    reset,
    trigger,
    formState: { errors, isValid }
  } = useForm<SpotFormData>({
    resolver,
    defaultValues: getDefaultValues(),
    mode: 'onBlur',
    reValidateMode: 'onChange'
  })

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'weatherData'
  })

  const onSubmit = async (data: SpotFormData) => {
    if (effectiveSpotRequestId === undefined) {
      return
    }

    const submittedForecast = await dispatch(
      submitSpotForecast({
        formData: data,
        isMini,
        spotRequestId: effectiveSpotRequestId
      })
    )

    if (submittedForecast) {
      setSelectedSpotForecast(submittedForecast)
    }
  }

  useEffect(() => {
    if (effectiveSpotRequestId !== undefined) {
      dispatch(fetchSpotForecasts(effectiveSpotRequestId))
    }
  }, [dispatch, effectiveSpotRequestId])

  useEffect(() => {
    setIsMini(spotRequest?.request_type === 'Mini')
  }, [spotRequest?.request_type])

  useEffect(() => {
    if (spotForecasts.length > 0 && !isInitialized) {
      const mostRecentForecast = spotForecasts[0]
      setSelectedSpotForecast(mostRecentForecast)
      reset(getForecastFormData(mostRecentForecast))
      setIsInitialized(true)
      return
    }

    if (spotForecasts.length === 0 && !isInitialized) {
      reset(requestDefaultValues)
      setIsInitialized(true)
    }
  }, [getForecastFormData, isInitialized, requestDefaultValues, reset, spotForecasts])

  useEffect(() => {
    setIsInitialized(false)
    setSelectedSpotForecast(undefined)
  }, [effectiveSpotRequestId])

  useEffect(() => {
    dispatch(fetchWxStations(getStations, StationSource.wildfire_one))
  }, [dispatch])

  useEffect(() => {
    return () => {
      dispatch(clearSpotForecastSubmitState())
    }
  }, [dispatch])

  useEffect(() => {
    // re-check fields whose requirements change when switching between Mini and Full SPOT
    const validateModeDependentFields = async () => {
      await trigger(['outlook', 'weatherData'])
    }

    validateModeDependentFields()
  }, [isMini, trigger])

  return (
    <Box sx={{ p: 3, maxWidth: 1400, mx: 'auto' }}>
      <Typography variant="h4" gutterBottom>
        Spot Forecast Form
      </Typography>

      <Box sx={{ mb: 2 }}>
        <FormControlLabel
          control={<Switch checked={isMini} onChange={e => setIsMini(e.target.checked)} />}
          label="Mini Spot"
        />
      </Box>

      {spotForecastsLoading && (
        <Alert severity="info" sx={{ mb: 2 }}>
          Loading saved spot forecasts...
        </Alert>
      )}

      {spotForecastsError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Unable to load saved spot forecasts.
        </Alert>
      )}

      <form onSubmit={handleSubmit(onSubmit)}>
        <Grid container spacing={3}>
          <SpotForecastHeader control={control} errors={errors} />
          <SpotForecastSynopsis control={control} errors={errors} />
          {!isMini && <SpotForecastSummaries control={control} errors={errors} />}
          <WeatherDataTable control={control} errors={errors} fields={fields} append={append} remove={remove} />
          <SpotForecastSections control={control} errors={errors} isMini={isMini} />

          {spotForecastSubmitError && (
            <Grid size={12}>
              <Alert severity="error">{spotForecastSubmitError}</Alert>
            </Grid>
          )}

          <Grid size={12}>
            <Button
              type="submit"
              variant="contained"
              size="large"
              fullWidth
              disabled={!isValid || spotForecastSubmitting || effectiveSpotRequestId === undefined}
            >
              {spotForecastSubmitting ? 'Submitting Spot Forecast...' : 'Submit Spot Forecast'}
            </Button>
          </Grid>
        </Grid>
      </form>
    </Box>
  )
}

export default SpotForecastForm
