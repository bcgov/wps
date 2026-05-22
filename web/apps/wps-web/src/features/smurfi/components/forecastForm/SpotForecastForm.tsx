import React, { useEffect, useState, useMemo } from 'react'
import { useForm, useFieldArray } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useDispatch, useSelector } from 'react-redux'
import { Alert, Grid, Typography, Button, Box, Switch, FormControlLabel } from '@mui/material'
import { fetchWxStations } from '@/features/stations/slices/stationsSlice'
import { AppDispatch } from '@/app/store'
import { RootState } from '@/app/rootReducer'
import { getDefaultValues, defaultWeatherRows } from '@/features/smurfi/constants/spotForecastDefaults'
import SpotForecastHeader from '@/features/smurfi/components/forecastForm/SpotForecastHeader'
import SpotForecastSynopsis from '@/features/smurfi/components/forecastForm/SpotForecastSynopsis'
import WeatherDataTable from '@/features/smurfi/components/forecastForm/WeatherDataTable'
import SpotForecastSummaries from '@/features/smurfi/components/forecastForm/SpotForecastSummaries'
import SpotForecastSections from '@/features/smurfi/components/forecastForm/SpotForecastSections'
import { SpotRequestOutput } from '@wps/api/SMURFIAPI'
import { createSchema, SpotFormData } from '@wps/api/schema/spotForecastSchema'
import { getStations, StationSource } from '@wps/api/stationAPI'
import { clearSpotForecastSubmitState, submitSpotForecast } from '@/features/smurfi/slices/smurfiSlice'

const toFormString = (value: number | string | null | undefined) =>
  value === null || value === undefined ? '' : String(value)

const formatFireNumbers = (fireNumbers: string[] | null | undefined) => fireNumbers?.join(', ') ?? ''

interface SpotForecastFormProps {
  spotRequest: SpotRequestOutput
  onSubmitSuccess?: () => void
}

const SpotForecastForm: React.FC<SpotForecastFormProps> = ({ spotRequest, onSubmitSuccess }) => {
  const dispatch: AppDispatch = useDispatch()
  const { spotForecastSubmitting, spotForecastSubmitError } = useSelector((state: RootState) => state.smurfi)
  const [isMini, setIsMini] = useState(false)
  const schema = useMemo(() => createSchema(isMini), [isMini])
  const resolver = useMemo(() => zodResolver(schema), [schema])

  const requestDefaultValues = useMemo<Partial<SpotFormData>>(() => {
    const defaultValues = getDefaultValues()

    return {
      ...defaultValues,
      fireProj: formatFireNumbers(spotRequest.fire_number),
      requestBy: spotRequest.requestor_name,
      latitude: toFormString(spotRequest.latitude),
      longitude: toFormString(spotRequest.longitude),
      slopeAspect: spotRequest.aspect ?? defaultValues.slopeAspect,
      elevation: toFormString(spotRequest.elevation),
      weatherData: defaultWeatherRows
    }
  }, [spotRequest])

  const {
    control,
    handleSubmit,
    reset,
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
    const submittedForecast = await dispatch(
      submitSpotForecast({
        formData: data,
        isMini,
        spotRequestId: spotRequest.id
      })
    )

    if (submittedForecast) {
      onSubmitSuccess?.()
    }
  }

  useEffect(() => {
    setIsMini(spotRequest.request_type === 'Mini')
  }, [spotRequest.request_type])

  useEffect(() => {
    reset(requestDefaultValues)
  }, [requestDefaultValues, reset])

  useEffect(() => {
    dispatch(fetchWxStations(getStations, StationSource.wildfire_one))
  }, [dispatch])

  useEffect(() => {
    return () => {
      dispatch(clearSpotForecastSubmitState())
    }
  }, [dispatch])

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
              disabled={!isValid || spotForecastSubmitting}
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
