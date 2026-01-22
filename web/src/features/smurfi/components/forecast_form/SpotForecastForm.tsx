import React, { useContext, useEffect, useState } from 'react'
import { useForm, useFieldArray } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useDispatch, useSelector } from 'react-redux'
import { Grid, Typography, Button, Box, Switch, FormControlLabel } from '@mui/material'
import { fetchWxStations } from '@/features/stations/slices/stationsSlice'
import { getStations, StationSource } from '@/api/stationAPI'
import { AppDispatch } from '@/app/store'
import { RootState } from '@/app/rootReducer'
import { UserContext } from '@/features/smurfi/contexts/UserContext'
import { createSchema, FormData } from '@/features/smurfi/schemas/spotForecastSchema'
import { getDefaultValues } from '@/features/smurfi/constants/spotForecastDefaults'
import { submitSpotForecast, clearSpotForecastSubmitState } from '@/features/smurfi/slices/smurfiSlice'
import SpotForecastHeader from '@/features/smurfi/components/forecast_form/SpotForecastHeader'
import SpotForecastSynopsis from '@/features/smurfi/components/forecast_form/SpotForecastSynopsis'
import WeatherDataTable from '@/features/smurfi/components/forecast_form/WeatherDataTable'
import SpotForecastSummaries from '@/features/smurfi/components/forecast_form/SpotForecastSummaries'
import SpotForecastSections from '@/features/smurfi/components/forecast_form/SpotForecastSections'

const SpotForecastForm: React.FC = () => {
  const user = useContext(UserContext)
  const dispatch: AppDispatch = useDispatch()
  const [isMini, setIsMini] = useState(false)

  const { spotForecastSubmitting, spotForecastSubmitError } = useSelector((state: RootState) => state.smurfi)

  const {
    control,
    handleSubmit,
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
    dispatch(submitSpotForecast({ formData: data, isMini }))
  }

  useEffect(() => {
    dispatch(fetchWxStations(getStations, StationSource.wildfire_one))
  }, [])

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
          {!isMini && <SpotForecastSummaries control={control} />}
          <WeatherDataTable control={control} errors={errors} fields={fields} append={append} remove={remove} />
          <SpotForecastSections control={control} errors={errors} isMini={isMini} />

          {/* Submit */}
          <Grid item xs={12}>
            <Button
              type="submit"
              variant="contained"
              size="large"
              fullWidth
              disabled={!isValid || spotForecastSubmitting}
            >
              {spotForecastSubmitting ? 'Submitting...' : 'Submit Spot Forecast'}
            </Button>
            {spotForecastSubmitError && (
              <Typography color="error" sx={{ mt: 1 }}>
                Error submitting forecast: {spotForecastSubmitError}
              </Typography>
            )}
          </Grid>
        </Grid>
      </form>
    </Box>
  )
}

export default SpotForecastForm
