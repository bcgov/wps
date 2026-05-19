import React from 'react'
import {
  Alert,
  Autocomplete,
  Box,
  Button,
  Checkbox,
  FormControl,
  FormControlLabel,
  FormHelperText,
  FormLabel,
  FormGroup,
  Grid,
  IconButton,
  InputAdornment,
  InputLabel,
  MenuItem,
  Radio,
  RadioGroup,
  Select,
  TextField,
  Tooltip
} from '@mui/material'
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined'
import { DateTime } from 'luxon'
import { Controller, FieldErrors, useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { AdapterLuxon } from '@mui/x-date-pickers/AdapterLuxon'
import { DatePicker, LocalizationProvider } from '@mui/x-date-pickers'
import {
  requestedFrequencyOptions,
  slopeAspectOptions,
  spotForecastTypes,
  spotRequestSchema,
  SpotRequestFormData,
  SpotRequestFormValues
} from '@wps/api/schema/spotRequestSchema'
import SpotRequestLocationField from '@/features/smurfi/components/request_form/SpotRequestLocationField'

interface SpotRequestFormProps {
  onCancel: () => void
  onSubmit?: (request: SpotRequestFormData) => void
}

const forecastTypeOptions: Record<SpotRequestFormValues['forecastType'], string> = {
  MINI_SPOT: 'Mini SPOT - Use for smaller requests where less detail is sufficient.',
  FULL_SPOT: 'Full SPOT - Use for requests where more detail is required.'
}

const getEmailErrorMessage = (errors: FieldErrors<SpotRequestFormValues>) => {
  const error = errors.emailDistributionList

  if (!error) {
    return undefined
  }

  if ('message' in error && typeof error.message === 'string') {
    return error.message
  }

  if (Array.isArray(error)) {
    return error.find(Boolean)?.message
  }

  return undefined
}

const defaultValues: SpotRequestFormValues = {
  fireNumber: '',
  forecastStartDate: DateTime.now().setZone('America/Vancouver'),
  forecastEndDate: DateTime.now().setZone('America/Vancouver').plus({ days: 5 }),
  forecastType: 'MINI_SPOT',
  emailDistributionList: [],
  requestedFrequency: [],
  location: null,
  geographicDescription: '',
  slopeAspect: 'North',
  elevation: '',
  additionalInformation: ''
}

const SpotRequestForm: React.FC<SpotRequestFormProps> = ({ onCancel, onSubmit }) => {
  const {
    control,
    handleSubmit,
    formState: { errors }
  } = useForm<SpotRequestFormValues, unknown, SpotRequestFormData>({
    resolver: zodResolver(spotRequestSchema),
    defaultValues,
    mode: 'onBlur',
    reValidateMode: 'onChange'
  })

  const handleValidSubmit = (data: SpotRequestFormData) => {
    onSubmit?.(data)
    console.log('Submitted Spot Request:', {
      ...data,
      forecastStartDate: data.forecastStartDate.toISO(),
      forecastEndDate: data.forecastEndDate.toISO(),
      elevation: Number(data.elevation)
    })
  }

  const emailErrorMessage = getEmailErrorMessage(errors)
  const locationErrorMessage =
    errors.location?.message ?? errors.location?.latitude?.message ?? errors.location?.longitude?.message

  return (
    <LocalizationProvider dateAdapter={AdapterLuxon}>
      <Box component="form" onSubmit={handleSubmit(handleValidSubmit)}>
        <Grid container spacing={2}>
          <Grid size={12}>
            <Alert severity="info">
              Forecasts are scheduled based on forecaster capacity. Your forecast may not start on the requested date;
              requests submitted for today will usually begin with tomorrow&apos;s forecast.
            </Alert>
          </Grid>

          <Grid size={{ xs: 12, sm: 6 }}>
            <Controller
              name="fireNumber"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Fire Number"
                  fullWidth
                  error={!!errors.fireNumber}
                  helperText={errors.fireNumber?.message}
                />
              )}
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <Controller
              name="emailDistributionList"
              control={control}
              render={({ field }) => (
                <Autocomplete<string, true, false, true>
                  multiple
                  freeSolo
                  options={[]}
                  value={field.value}
                  onBlur={field.onBlur}
                  onChange={(_, value) => field.onChange(value)}
                  renderInput={params => (
                    <TextField
                      {...params}
                      label="Email Distribution List"
                      error={!!emailErrorMessage}
                      helperText={emailErrorMessage}
                    />
                  )}
                />
              )}
            />
          </Grid>

          <Grid size={{ xs: 12, sm: 6 }}>
            <Controller
              name="forecastStartDate"
              control={control}
              render={({ field }) => (
                <DatePicker
                  label="Desired Forecast Start Date"
                  value={field.value}
                  onChange={field.onChange}
                  timezone="America/Vancouver"
                  slotProps={{
                    textField: {
                      fullWidth: true,
                      error: !!errors.forecastStartDate,
                      helperText: errors.forecastStartDate?.message
                    }
                  }}
                />
              )}
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <Controller
              name="forecastEndDate"
              control={control}
              render={({ field }) => (
                <DatePicker
                  label="Forecast End Date"
                  value={field.value}
                  onChange={field.onChange}
                  timezone="America/Vancouver"
                  slotProps={{
                    textField: {
                      fullWidth: true,
                      error: !!errors.forecastEndDate,
                      helperText: errors.forecastEndDate?.message
                    }
                  }}
                />
              )}
            />
          </Grid>

          <Grid size={12}>
            <Controller
              name="forecastType"
              control={control}
              render={({ field }) => (
                <FormControl error={!!errors.forecastType}>
                  <FormLabel>
                    <Box component="span" sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5 }}>
                      Forecast Type
                      <Tooltip
                        placement="right-start"
                        arrow
                        title="Mini SPOT is for smaller, lower-complexity requests and does not include daily forecast summaries or a written 3-5 day outlook."
                      >
                        <IconButton aria-label="Forecast type information" size="small" sx={{ p: 0.25 }}>
                          <InfoOutlinedIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </FormLabel>
                  <RadioGroup {...field}>
                    {spotForecastTypes.map(type => (
                      <FormControlLabel key={type} value={type} control={<Radio />} label={forecastTypeOptions[type]} />
                    ))}
                  </RadioGroup>
                  <FormHelperText>{errors.forecastType?.message}</FormHelperText>
                </FormControl>
              )}
            />
          </Grid>

          <Grid size={12}>
            <Controller
              name="requestedFrequency"
              control={control}
              render={({ field }) => (
                <FormControl error={!!errors.requestedFrequency}>
                  <FormLabel>Requested Frequency</FormLabel>
                  <FormGroup row>
                    {requestedFrequencyOptions.map(day => (
                      <FormControlLabel
                        key={day}
                        control={
                          <Checkbox
                            checked={field.value.includes(day)}
                            onChange={event => {
                              const nextValue = event.target.checked
                                ? [...field.value, day]
                                : field.value.filter(selectedDay => selectedDay !== day)
                              field.onChange(nextValue)
                            }}
                          />
                        }
                        label={day}
                      />
                    ))}
                  </FormGroup>
                  <FormHelperText>{errors.requestedFrequency?.message}</FormHelperText>
                </FormControl>
              )}
            />
          </Grid>

          <Grid size={{ xs: 12, sm: 6 }}>
            <Controller
              name="slopeAspect"
              control={control}
              render={({ field }) => (
                <FormControl fullWidth error={!!errors.slopeAspect}>
                  <InputLabel id="slope-aspect-label">Slope/Aspect</InputLabel>
                  <Select {...field} labelId="slope-aspect-label" label="Slope/Aspect">
                    {slopeAspectOptions.map(option => (
                      <MenuItem key={option} value={option}>
                        {option}
                      </MenuItem>
                    ))}
                  </Select>
                  <FormHelperText>{errors.slopeAspect?.message}</FormHelperText>
                </FormControl>
              )}
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <Controller
              name="elevation"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Elevation"
                  type="number"
                  fullWidth
                  error={!!errors.elevation}
                  helperText={errors.elevation?.message}
                  slotProps={{
                    input: {
                      endAdornment: <InputAdornment position="end">m</InputAdornment>
                    }
                  }}
                />
              )}
            />
          </Grid>

          <Grid size={12}>
            <Controller
              name="geographicDescription"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Geographic Description"
                  fullWidth
                  multiline
                  minRows={2}
                  error={!!errors.geographicDescription}
                  helperText={errors.geographicDescription?.message}
                />
              )}
            />
          </Grid>

          <Grid size={12}>
            <Controller
              name="location"
              control={control}
              render={({ field }) => (
                <SpotRequestLocationField
                  value={field.value}
                  onChange={field.onChange}
                  onBlur={field.onBlur}
                  errorMessage={locationErrorMessage}
                />
              )}
            />
          </Grid>

          <Grid size={12}>
            <Controller
              name="additionalInformation"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Any additional information or requests for the forecaster?"
                  fullWidth
                  multiline
                  minRows={4}
                />
              )}
            />
          </Grid>

          <Grid size={12}>
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
              <Button onClick={onCancel}>Cancel</Button>
              <Button type="submit" variant="contained">
                Submit Request
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Box>
    </LocalizationProvider>
  )
}

export default SpotRequestForm
