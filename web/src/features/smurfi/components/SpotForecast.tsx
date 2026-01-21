// src/components/SpotForecastForm.tsx
import React, { useContext } from 'react'
import { useForm, Controller, useFieldArray } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'

import { z } from 'zod'
import {
  Grid,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Box,
  InputAdornment
} from '@mui/material'
import { AdapterLuxon } from '@mui/x-date-pickers/AdapterLuxon'
import { LocalizationProvider, DateTimePicker } from '@mui/x-date-pickers'
import { DateTime } from 'luxon'
import AddIcon from '@mui/icons-material/Add'
import DeleteIcon from '@mui/icons-material/Delete'
import { PST_UTC_OFFSET } from '@/utils/constants'

interface UserContextType {
  name: string
  email: string
  phone: string
}
const UserContext = React.createContext<UserContextType>({
  name: 'Elizabeth Chapman',
  email: 'BCWS.KFCFireWeather@gov.bc.ca',
  phone: '250-851-6784'
})

// ────────────────────────────────────────────────
// Zod Schema
// ────────────────────────────────────────────────

const weatherRowSchema = z.object({
  dateTime: z.string().min(1, 'Date/Time required'),
  temp: z
    .string()
    .optional()
    .refine(val => !val || !isNaN(Number(val)), 'Must be a number'),
  rh: z
    .string()
    .optional()
    .refine(val => {
      if (!val) return true
      const num = Number(val)
      return !isNaN(num) && num >= 0 && num <= 100
    }, 'RH must be a number between 0 and 100'),
  wind: z.string().optional(),
  rain: z.string().optional(),
  chanceRain: z.string().optional()
})

const schema = z.object({
  issuedDate: z.custom<DateTime>((val): val is DateTime => DateTime.isDateTime(val) && val.isValid, {
    message: 'Invalid date/time'
  }),
  expiryDate: z.custom<DateTime>((val): val is DateTime => DateTime.isDateTime(val) && val.isValid, {
    message: 'Invalid date/time'
  }),
  fireProj: z.string().min(1, 'Required'),
  requestBy: z.string().refine(val => val.length > 0, 'Required'),
  forecastBy: z.string().refine(val => val.length > 0, 'Required'),
  email: z.string().email('Invalid email'),
  phone: z.string().refine(val => val.length > 0, 'Required'),
  city: z.string().refine(val => val.length > 0, 'Required'),
  stns: z.string().optional(),
  coordinates: z.string().optional(),
  slopeAspect: z.string().optional(),
  valley: z.string().optional(),
  elevation: z.string().optional(),
  size: z.string().optional(),
  synopsis: z.string().refine(val => val.length > 0, 'Required'),
  afternoonForecast: z.string().optional(),
  tonightForecast: z.string().optional(),
  tomorrowForecast: z.string().optional(),
  weatherData: z.array(weatherRowSchema).min(1, 'At least one weather entry required'),
  inversionVenting: z.string().optional(),
  outlook: z.string().optional(),
  confidenceDiscussion: z.string().optional()
})

type FormData = z.infer<typeof schema>

// ────────────────────────────────────────────────
// Default values (pre-filled like your example)
// ────────────────────────────────────────────────

const defaultDateTimes = [
  DateTime.now().setZone('America/Vancouver').set({ hour: 16, minute: 0 }),
  DateTime.now().setZone('America/Vancouver').set({ hour: 19, minute: 0 }),
  DateTime.now().setZone('America/Vancouver').set({ hour: 0, minute: 0 }),
  DateTime.now().setZone('America/Vancouver').plus({ days: 1 }).set({ hour: 10, minute: 0 }),
  DateTime.now().setZone('America/Vancouver').plus({ days: 1 }).set({ hour: 13, minute: 0 }),
  DateTime.now().setZone('America/Vancouver').plus({ days: 1 }).set({ hour: 16, minute: 0 }),
  DateTime.now().setZone('America/Vancouver').plus({ days: 1 }).set({ hour: 19, minute: 0 }),
  DateTime.now().setZone('America/Vancouver').plus({ days: 1 }).set({ hour: 0, minute: 0 }),
  DateTime.now().setZone('America/Vancouver').plus({ days: 2 }).set({ hour: 16, minute: 0 })
]

const defaultWeatherRows: FormData['weatherData'] = defaultDateTimes.map(dt => ({
  dateTime: dt.toFormat('yyyy-MM-dd HH:mm'),
  temp: '',
  rh: '',
  wind: '',
  rain: '-',
  chanceRain: '-'
}))

const SpotForecastForm: React.FC = () => {
  const user = useContext(UserContext)

  const {
    control,
    handleSubmit,
    formState: { errors }
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      issuedDate: DateTime.now().setZone('America/Vancouver'),
      expiryDate: DateTime.now().setZone('America/Vancouver').plus({ days: 1 }).endOf('day'),
      fireProj: 'Peterson Creek burn',
      requestBy: 'Conlan Sprickerhoff',
      forecastBy: user.name,
      email: user.email,
      phone: user.phone,
      city: 'Kamloops',
      stns: 'Afton (1123m)',
      coordinates: '50 39.612, -120 20.088',
      slopeAspect: 'South',
      valley: 'W to E',
      elevation: '545',
      size: '5 to 20 ha',
      synopsis: '',
      afternoonForecast: 'Mainly sunny in the morning then increasing afternoon cloud. MAX TEMP 11C, MIN RH 40%',
      tonightForecast: 'Mainly clear. MIN TEMP -2C. MAX RH 90%.',
      tomorrowForecast: 'Cloudy. TEMP 12C. MIN RH 40%.',
      weatherData: defaultWeatherRows,
      inversionVenting: '',
      outlook: '',
      confidenceDiscussion: ''
    },
    mode: 'onSubmit',
    reValidateMode: 'onChange'
  })

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'weatherData'
  })

  const onSubmit = (data: FormData) => {
    // For demo: log the data with nice formatting
    console.log('Submitted Forecast:', {
      ...data,
      issuedDate: data.issuedDate.toISO(),
      expiryDate: data.expiryDate.toISO(),
      weatherData: data.weatherData.map(row => ({
        ...row,
        temp: row.temp ? Number(row.temp) : '-',
        rh: row.rh ? Number(row.rh) : '-'
      }))
    })

    // → Here you would:
    // 1. Send to your backend API
    // 2. Generate .docx file (using docx.js or similar)
    // 3. Show success toast, etc.
    alert('Forecast submitted! Check console for formatted data.')
  }

  return (
    <LocalizationProvider dateAdapter={AdapterLuxon}>
      <Box sx={{ p: 3, maxWidth: 1400, mx: 'auto' }}>
        <Typography variant="h4" gutterBottom>
          BC Wildfire Service Spot Forecast Form
        </Typography>

        <form onSubmit={handleSubmit(onSubmit)}>
          <Grid container spacing={3}>
            {/* ─── Header ──────────────────────────────────────── */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Header Information
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <Controller
                        name="issuedDate"
                        control={control}
                        render={({ field }) => (
                          <DateTimePicker
                            label="Date/Time Issued"
                            value={field.value}
                            onChange={field.onChange}
                            timezone="America/Vancouver"
                            slotProps={{
                              textField: {
                                fullWidth: true,
                                error: !!errors.issuedDate,
                                helperText: errors.issuedDate?.message
                              }
                            }}
                          />
                        )}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Controller
                        name="expiryDate"
                        control={control}
                        render={({ field }) => (
                          <DateTimePicker
                            label="Default Expiry"
                            value={field.value}
                            onChange={field.onChange}
                            timezone="America/Vancouver"
                            slotProps={{
                              textField: {
                                fullWidth: true,
                                error: !!errors.expiryDate,
                                helperText: errors.expiryDate?.message
                              }
                            }}
                          />
                        )}
                      />
                    </Grid>

                    <Grid item xs={12} sm={6}>
                      <Controller
                        name="fireProj"
                        control={control}
                        render={({ field }) => (
                          <TextField
                            {...field}
                            label="Fire/Proj #"
                            fullWidth
                            error={!!errors.fireProj}
                            helperText={errors.fireProj?.message}
                          />
                        )}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Controller
                        name="requestBy"
                        control={control}
                        render={({ field }) => (
                          <TextField
                            {...field}
                            label="Request by"
                            fullWidth
                            error={!!errors.requestBy}
                            helperText={errors.requestBy?.message}
                          />
                        )}
                      />
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <Controller
                        name="forecastBy"
                        control={control}
                        render={({ field }) => <TextField {...field} label="Forecast by" fullWidth disabled />}
                      />
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <Controller
                        name="email"
                        control={control}
                        render={({ field }) => <TextField {...field} label="Email" fullWidth disabled />}
                      />
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <Controller
                        name="phone"
                        control={control}
                        render={({ field }) => <TextField {...field} label="Phone" fullWidth disabled />}
                      />
                    </Grid>

                    {/* Location / Geometry fields */}
                    <Grid item xs={12} sm={6}>
                      <Controller
                        name="city"
                        control={control}
                        render={({ field }) => (
                          <TextField
                            {...field}
                            label="City"
                            fullWidth
                            error={!!errors.city}
                            helperText={errors.city?.message}
                          />
                        )}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Controller
                        name="stns"
                        control={control}
                        render={({ field }) => <TextField {...field} label="Representative Stns" fullWidth />}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Controller
                        name="coordinates"
                        control={control}
                        render={({ field }) => <TextField {...field} label="Coordinates (approx)" fullWidth />}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Controller
                        name="slopeAspect"
                        control={control}
                        render={({ field }) => <TextField {...field} label="Slope/Aspect" fullWidth />}
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <Controller
                        name="valley"
                        control={control}
                        render={({ field }) => <TextField {...field} label="Valley" fullWidth />}
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <Controller
                        name="elevation"
                        control={control}
                        render={({ field }) => (
                          <TextField
                            {...field}
                            label="Elevation"
                            fullWidth
                            InputProps={{
                              endAdornment: <InputAdornment position="end">m</InputAdornment>
                            }}
                          />
                        )}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Controller
                        name="size"
                        control={control}
                        render={({ field }) => (
                          <TextField
                            {...field}
                            label="Size (ha)"
                            fullWidth
                            InputProps={{
                              endAdornment: <InputAdornment position="end">ha</InputAdornment>
                            }}
                          />
                        )}
                      />
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>

            {/* ─── Synopsis ────────────────────────────────────── */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Synopsis
                  </Typography>
                  <Controller
                    name="synopsis"
                    control={control}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        multiline
                        rows={5}
                        fullWidth
                        error={!!errors.synopsis}
                        helperText={errors.synopsis?.message}
                        placeholder="A building ridge of high pressure over coastal BC will support..."
                      />
                    )}
                  />
                </CardContent>
              </Card>
            </Grid>

            {/* ─── Forecast Summaries ──────────────────────────── */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Forecast Summaries
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <Controller
                        name="afternoonForecast"
                        control={control}
                        render={({ field }) => <TextField {...field} label="Afternoon" fullWidth multiline rows={2} />}
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <Controller
                        name="tonightForecast"
                        control={control}
                        render={({ field }) => <TextField {...field} label="Tonight" fullWidth multiline rows={2} />}
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <Controller
                        name="tomorrowForecast"
                        control={control}
                        render={({ field }) => <TextField {...field} label="Tomorrow" fullWidth multiline rows={2} />}
                      />
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>

            {/* ─── Weather Table (with dynamic rows) ───────────── */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                    <Typography variant="h6">Weather Data</Typography>
                    <Button
                      variant="outlined"
                      startIcon={<AddIcon />}
                      onClick={() =>
                        append({
                          dateTime: DateTime.now().toFormat('yyyy-MM-dd HH:mm'),
                          temp: '',
                          rh: '',
                          wind: '',
                          rain: '-',
                          chanceRain: '-'
                        })
                      }
                    >
                      Add Row
                    </Button>
                  </Box>

                  <TableContainer component={Paper}>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Date/Time (PDT)</TableCell>
                          <TableCell>Temp (C)</TableCell>
                          <TableCell>RH (%)</TableCell>
                          <TableCell>Wind (km/h)</TableCell>
                          <TableCell>Rain (mm)</TableCell>
                          <TableCell>Chance Rain</TableCell>
                          <TableCell width={60} />
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {fields.map((field, index) => (
                          <TableRow key={field.id}>
                            <TableCell>
                              <Controller
                                name={`weatherData.${index}.dateTime`}
                                control={control}
                                render={({ field }) => (
                                  <TextField
                                    {...field}
                                    size="small"
                                    fullWidth
                                    error={!!errors.weatherData?.[index]?.dateTime}
                                    helperText={errors.weatherData?.[index]?.dateTime?.message}
                                  />
                                )}
                              />
                            </TableCell>
                            <TableCell>
                              <Controller
                                name={`weatherData.${index}.temp`}
                                control={control}
                                render={({ field }) => (
                                  <TextField
                                    {...field}
                                    type="number"
                                    size="small"
                                    fullWidth
                                    error={!!errors.weatherData?.[index]?.temp}
                                    helperText={errors.weatherData?.[index]?.temp?.message}
                                  />
                                )}
                              />
                            </TableCell>
                            <TableCell>
                              <Controller
                                name={`weatherData.${index}.rh`}
                                control={control}
                                render={({ field }) => (
                                  <TextField
                                    {...field}
                                    type="number"
                                    size="small"
                                    fullWidth
                                    error={!!errors.weatherData?.[index]?.rh}
                                    helperText={errors.weatherData?.[index]?.rh?.message}
                                  />
                                )}
                              />
                            </TableCell>
                            <TableCell>
                              <Controller
                                name={`weatherData.${index}.wind`}
                                control={control}
                                render={({ field }) => <TextField {...field} size="small" fullWidth />}
                              />
                            </TableCell>
                            <TableCell>
                              <Controller
                                name={`weatherData.${index}.rain`}
                                control={control}
                                render={({ field }) => <TextField {...field} size="small" fullWidth />}
                              />
                            </TableCell>
                            <TableCell>
                              <Controller
                                name={`weatherData.${index}.chanceRain`}
                                control={control}
                                render={({ field }) => <TextField {...field} size="small" fullWidth />}
                              />
                            </TableCell>
                            <TableCell>
                              <IconButton size="small" color="error" onClick={() => remove(index)}>
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>

                  {errors.weatherData && typeof errors.weatherData === 'string' && (
                    <Typography color="error" sx={{ mt: 1 }}>
                      {errors.weatherData}
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>

            {/* ─── Inversion & Venting ─────────────────────────── */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Inversion & Venting
                  </Typography>
                  <Controller
                    name="inversionVenting"
                    control={control}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        multiline
                        rows={4}
                        fullWidth
                        placeholder="The morning inversion will lift by 10 AM once temperatures rise..."
                      />
                    )}
                  />
                </CardContent>
              </Card>
            </Grid>

            {/* ─── Outlook ─────────────────────────────────────── */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Outlook (3-5 Day)
                  </Typography>
                  <Controller
                    name="outlook"
                    control={control}
                    render={({ field }) => <TextField {...field} multiline rows={4} fullWidth />}
                  />
                </CardContent>
              </Card>
            </Grid>

            {/* ─── Confidence/Discussion ───────────────────────── */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Confidence / Discussion
                  </Typography>
                  <Controller
                    name="confidenceDiscussion"
                    control={control}
                    render={({ field }) => <TextField {...field} multiline rows={4} fullWidth />}
                  />
                </CardContent>
              </Card>
            </Grid>

            {/* Submit */}
            <Grid item xs={12}>
              <Button type="submit" variant="contained" size="large" fullWidth>
                Submit Spot Forecast
              </Button>
            </Grid>
          </Grid>
        </form>
      </Box>
    </LocalizationProvider>
  )
}

export default SpotForecastForm
