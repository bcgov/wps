import React, { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Autocomplete,
  Box,
  Button,
  Checkbox,
  Chip,
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
import GroupsIcon from '@mui/icons-material/Groups'
import { DateTime } from 'luxon'
import { Controller, FieldErrors, useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { DatePicker } from '@mui/x-date-pickers-pro'
import {
  requestedFrequencyOptions,
  slopeAspectOptions,
  spotForecastTypes,
  spotRequestSchema,
  SpotRequestFormData,
  SpotRequestFormValues
} from '@wps/api/schema/spotRequestSchema'
import { DistributionGroup, SpotRequestOutput, SpotRequestStatus, getDistributionGroups } from '@wps/api/SMURFIAPI'
import { AppDispatch } from '@/app/store'
import { RootState, selectFireCentres } from '@/app/rootReducer'
import { clearSpotRequestSubmitState, submitSpotRequest } from '@/features/smurfi/slices/smurfiSlice'
import SpotRequestLocationField from '@/features/smurfi/components/requestForm/SpotRequestLocationField'
import { useDispatch, useSelector } from 'react-redux'

interface SpotRequestFormProps {
  onCancel: () => void
  onSubmit?: (request: SpotRequestOutput) => void
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

const getFireNumberErrorMessage = (errors: FieldErrors<SpotRequestFormValues>) => {
  const error = errors.fireNumbers

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

const splitFireNumberInput = (value: string) =>
  value
    .split(/[,\s]+/)
    .map(fireNumber => fireNumber.trim())
    .filter(Boolean)

const normalizeFireNumberValues = (values: string[]) => {
  const seenFireNumbers = new Set<string>()
  return values.flatMap(splitFireNumberInput).filter(fireNumber => {
    const normalizedFireNumber = fireNumber.toUpperCase()
    if (seenFireNumbers.has(normalizedFireNumber)) {
      return false
    }
    seenFireNumbers.add(normalizedFireNumber)
    return true
  })
}

const splitEmailInput = (value: string) =>
  value
    .split(/\s+/)
    .map(email => email.trim())
    .filter(Boolean)

const normalizeEmailValues = (values: string[]) => {
  const seenEmails = new Set<string>()
  return values.flatMap(splitEmailInput).filter(email => {
    const normalizedEmail = email.toLowerCase()
    if (seenEmails.has(normalizedEmail)) {
      return false
    }
    seenEmails.add(normalizedEmail)
    return true
  })
}

const defaultValues: SpotRequestFormValues = {
  fireNumbers: [],
  fireCentreId: 0,
  forecastStartDate: DateTime.now().setZone('America/Vancouver'),
  forecastEndDate: DateTime.now().setZone('America/Vancouver').plus({ days: 5 }),
  forecastType: 'MINI_SPOT',
  emailDistributionList: [],
  distributionGroupIds: [],
  requestedFrequency: [],
  location: null,
  geographicDescription: '',
  slopeAspect: 'North',
  elevation: '',
  additionalInformation: ''
}

type DistributionItem = string | DistributionGroup
const isGroup = (item: DistributionItem): item is DistributionGroup => typeof item !== 'string'

const SpotRequestForm: React.FC<SpotRequestFormProps> = ({ onCancel, onSubmit }) => {
  const dispatch: AppDispatch = useDispatch()
  const { fireCentres, loading: fireCentresLoading } = useSelector(selectFireCentres)
  const { spotRequestSubmitting, spotRequestSubmitError, spotRequests } = useSelector(
    (state: RootState) => state.smurfi
  )
  const [fireNumberInputValue, setFireNumberInputValue] = useState('')
  const [emailInputValue, setEmailInputValue] = useState('')
  const [distributionGroups, setDistributionGroups] = useState<DistributionGroup[]>([])
  const [distributionItems, setDistributionItems] = useState<DistributionItem[]>([])
  const existingMapSpotRequests = useMemo(
    () =>
      spotRequests.filter(
        spotRequest =>
          spotRequest.status !== SpotRequestStatus.COMPLETE && spotRequest.status !== SpotRequestStatus.ARCHIVED
      ),
    [spotRequests]
  )
  const {
    control,
    handleSubmit,
    setValue,
    formState: { errors }
  } = useForm<SpotRequestFormValues, unknown, SpotRequestFormData>({
    resolver: zodResolver(spotRequestSchema),
    defaultValues,
    mode: 'onBlur',
    reValidateMode: 'onChange'
  })

  useEffect(() => {
    getDistributionGroups().then(setDistributionGroups).catch(() => setDistributionGroups([]))
  }, [])

  useEffect(() => {
    return () => {
      dispatch(clearSpotRequestSubmitState())
    }
  }, [dispatch])

  const handleDistributionChange = (items: DistributionItem[]) => {
    setDistributionItems(items)
    setValue('emailDistributionList', items.filter((i): i is string => !isGroup(i)), { shouldValidate: true })
    setValue('distributionGroupIds', items.filter(isGroup).map(g => g.id), { shouldValidate: true })
  }

  const handleValidSubmit = async (data: SpotRequestFormData) => {
    const submittedSpotRequest = await dispatch(submitSpotRequest(data))
    if (submittedSpotRequest) {
      onSubmit?.(submittedSpotRequest)
    }
  }

  const emailErrorMessage = getEmailErrorMessage(errors)
  const fireNumberErrorMessage = getFireNumberErrorMessage(errors)
  const locationErrorMessage =
    errors.location?.message ?? errors.location?.latitude?.message ?? errors.location?.longitude?.message

  return (
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
            name="fireNumbers"
            control={control}
            render={({ field }) => {
              const commitFireNumberInput = () => {
                if (fireNumberInputValue.trim()) {
                  field.onChange(normalizeFireNumberValues([...field.value, fireNumberInputValue]))
                  setFireNumberInputValue('')
                }
              }

              return (
                <Autocomplete<string, true, false, true>
                  multiple
                  freeSolo
                  options={[]}
                  value={field.value}
                  inputValue={fireNumberInputValue}
                  onBlur={() => {
                    commitFireNumberInput()
                    field.onBlur()
                  }}
                  onChange={(_, value) => {
                    field.onChange(normalizeFireNumberValues(value))
                    setFireNumberInputValue('')
                  }}
                  onInputChange={(_, value, reason) => {
                    if (reason !== 'input') {
                      setFireNumberInputValue(value)
                      return
                    }
                    if (/[,\s]/.test(value)) {
                      field.onChange(normalizeFireNumberValues([...field.value, value]))
                      setFireNumberInputValue('')
                      return
                    }
                    setFireNumberInputValue(value)
                  }}
                  renderInput={params => (
                    <TextField
                      {...params}
                      label="Fire Numbers"
                      error={!!fireNumberErrorMessage}
                      helperText={fireNumberErrorMessage}
                    />
                  )}
                />
              )
            }}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Controller
            name="fireCentreId"
            control={control}
            render={({ field }) => (
              <FormControl fullWidth error={!!errors.fireCentreId}>
                <InputLabel id="fire-centre-label">Fire Centre</InputLabel>
                <Select
                  {...field}
                  labelId="fire-centre-label"
                  label="Fire Centre"
                  value={field.value || ''}
                  disabled={fireCentresLoading}
                  onChange={event => field.onChange(Number(event.target.value))}
                >
                  <MenuItem value={0} disabled>
                    Select a fire centre
                  </MenuItem>
                  {fireCentres.map(fireCentre => (
                    <MenuItem key={fireCentre.id} value={fireCentre.id}>
                      {fireCentre.name}
                    </MenuItem>
                  ))}
                </Select>
                <FormHelperText>{errors.fireCentreId?.message}</FormHelperText>
              </FormControl>
            )}
          />
        </Grid>

        <Grid size={12}>
          <Autocomplete<DistributionItem, true, false, true>
            multiple
            freeSolo
            options={distributionGroups}
            value={distributionItems}
            inputValue={emailInputValue}
            getOptionLabel={option => (isGroup(option) ? option.name : option)}
            isOptionEqualToValue={(option, value) =>
              isGroup(option) && isGroup(value) ? option.id === value.id : option === value
            }
            onBlur={() => {
              if (emailInputValue.trim()) {
                const normalized = normalizeEmailValues([
                  ...distributionItems.filter((i): i is string => !isGroup(i)),
                  emailInputValue
                ])
                handleDistributionChange([...distributionItems.filter(isGroup), ...normalized])
                setEmailInputValue('')
              }
            }}
            onChange={(_, value) => {
              const emails = value.filter((i): i is string => !isGroup(i))
              const groups = value.filter(isGroup)
              handleDistributionChange([...groups, ...normalizeEmailValues(emails)])
              setEmailInputValue('')
            }}
            onInputChange={(_, value, reason) => {
              if (reason !== 'input') {
                setEmailInputValue(value)
                return
              }
              if (/\s/.test(value)) {
                const normalized = normalizeEmailValues([
                  ...distributionItems.filter((i): i is string => !isGroup(i)),
                  value
                ])
                handleDistributionChange([...distributionItems.filter(isGroup), ...normalized])
                setEmailInputValue('')
                return
              }
              setEmailInputValue(value)
            }}
            renderTags={(value, getTagProps) =>
              value.map((item, index) =>
                isGroup(item) ? (
                  <Chip
                    key={item.id}
                    label={item.name}
                    icon={<GroupsIcon />}
                    color="primary"
                    variant="outlined"
                    size="small"
                    {...getTagProps({ index })}
                  />
                ) : (
                  <Chip key={item} label={item} size="small" {...getTagProps({ index })} />
                )
              )
            }
            renderInput={params => (
              <TextField
                {...params}
                label="Email Distribution List"
                error={!!emailErrorMessage}
                helperText={emailErrorMessage}
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
                existingSpotRequests={existingMapSpotRequests}
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

        {spotRequestSubmitError && (
          <Grid size={12}>
            <Alert severity="error">{spotRequestSubmitError}</Alert>
          </Grid>
        )}

        <Grid size={12}>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
            <Button onClick={onCancel} disabled={spotRequestSubmitting}>
              Cancel
            </Button>
            <Button type="submit" variant="contained" disabled={spotRequestSubmitting}>
              {spotRequestSubmitting ? 'Submitting...' : 'Submit Request'}
            </Button>
          </Box>
        </Grid>
      </Grid>
    </Box>
  )
}

export default SpotRequestForm
