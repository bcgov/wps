import React, { useEffect, useState, useMemo } from 'react'
import { useForm, useFieldArray } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useDispatch, useSelector } from 'react-redux'
import { Alert, Grid, Button, Box, FormControlLabel, FormControl, FormLabel, RadioGroup, Radio } from '@mui/material'
import { AppDispatch } from '@/app/store'
import { getDefaultValues, defaultWeatherRows } from '@/features/smurfi/constants/spotForecastDefaults'
import SpotForecastHeader from '@/features/smurfi/components/forecastForm/SpotForecastHeader'
import SpotForecastSynopsis from '@/features/smurfi/components/forecastForm/SpotForecastSynopsis'
import WeatherDataTable from '@/features/smurfi/components/forecastForm/WeatherDataTable'
import SpotForecastSummaries from '@/features/smurfi/components/forecastForm/SpotForecastSummaries'
import SpotForecastSections from '@/features/smurfi/components/forecastForm/SpotForecastSections'
import { SpotRequestOutput } from '@wps/api/SMURFIAPI'
import { createSchema, SpotFormData } from '@wps/api/schema/spotForecastSchema'
import { clearSpotForecastSubmitState, submitSpotForecast, selectSmurfi } from '@/features/smurfi/slices/smurfiSlice'

const toFormString = (value: number | string | null | undefined) =>
  value === null || value === undefined ? '' : String(value)

const formatFireNumbers = (fireNumbers: string[] | null | undefined) => fireNumbers?.join(', ') ?? ''

interface SpotForecastFormProps {
  spotRequest: SpotRequestOutput
  onSubmitSuccess?: () => void
}

const SpotForecastForm: React.FC<SpotForecastFormProps> = ({ spotRequest, onSubmitSuccess }) => {
  const dispatch: AppDispatch = useDispatch()
  const { spotForecastSubmitting, spotForecastSubmitError } = useSelector(selectSmurfi)
  const [isMini, setIsMini] = useState(false)
  const schema = useMemo(() => createSchema(isMini), [isMini])
  const resolver = useMemo(() => zodResolver(schema), [schema])

  const defaultValues = useMemo<Partial<SpotFormData>>(() => {
    const baseDefaults = getDefaultValues()

    return {
      ...baseDefaults,
      fireProj: formatFireNumbers(spotRequest.fire_number),
      requestBy: spotRequest.requestor_name,
      latitude: toFormString(spotRequest.latitude.toFixed(4)),
      longitude: toFormString(spotRequest.longitude.toFixed(4)),
      slopeAspect: spotRequest.aspect ?? baseDefaults.slopeAspect,
      elevation: toFormString(spotRequest.elevation),
      weatherData: defaultWeatherRows
    }
  }, [spotRequest])

  const {
    control,
    handleSubmit,
    reset,
    formState: { errors, submitCount }
  } = useForm<SpotFormData>({
    resolver,
    defaultValues,
    mode: 'onBlur',
    reValidateMode: 'onChange'
  })

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'weatherData'
  })
  const hasValidationErrors = Object.keys(errors).length > 0

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
    reset(defaultValues)
  }, [defaultValues, reset])

  useEffect(() => {
    return () => {
      dispatch(clearSpotForecastSubmitState())
    }
  }, [dispatch])

  return (
    <Box sx={{ p: 3, width: '100%' }}>
      <Box sx={{ mb: 2 }}>
        <FormControl>
          <FormLabel>Forecast Type</FormLabel>
          <RadioGroup row value={isMini ? 'mini' : 'full'} onChange={event => setIsMini(event.target.value === 'mini')}>
            <FormControlLabel value="mini" control={<Radio />} label="Mini Spot" />
            <FormControlLabel value="full" control={<Radio />} label="Full Spot" />
          </RadioGroup>
        </FormControl>
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
            {submitCount > 0 && hasValidationErrors && (
              <Grid size={12}>
                <Alert severity="error">
                  Some required fields are missing or invalid. Review the highlighted fields above.
                </Alert>
              </Grid>
            )}
            <Button type="submit" variant="contained" size="large" fullWidth disabled={spotForecastSubmitting}>
              {spotForecastSubmitting ? 'Submitting Spot Forecast...' : 'Submit Spot Forecast'}
            </Button>
          </Grid>
        </Grid>
      </form>
    </Box>
  )
}

export default SpotForecastForm
