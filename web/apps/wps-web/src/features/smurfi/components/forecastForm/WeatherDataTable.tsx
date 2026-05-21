import React from 'react'
import { Control, UseFieldArrayReturn, FieldErrors, FieldPath } from 'react-hook-form'
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Box
} from '@mui/material'
import { DateTime } from 'luxon'
import AddIcon from '@mui/icons-material/Add'
import DeleteIcon from '@mui/icons-material/Delete'
import { SpotFormData } from '@wps/api/schema/spotForecastSchema'
import WeatherDataCell from '@/features/smurfi/components/forecastForm/WeatherDataCell'

interface WeatherDataTableProps {
  control: Control<SpotFormData>
  errors: FieldErrors<SpotFormData>
  fields: UseFieldArrayReturn<SpotFormData, 'weatherData'>['fields']
  append: UseFieldArrayReturn<SpotFormData, 'weatherData'>['append']
  remove: UseFieldArrayReturn<SpotFormData, 'weatherData'>['remove']
  readOnly?: boolean
}

const dateCellSx = { width: 175, minWidth: 175 }
const compactWeatherCellSx = { width: 90, minWidth: 90 }
const windCellSx = { width: 190, minWidth: 190 }

const WeatherDataTable: React.FC<WeatherDataTableProps> = ({
  control,
  errors,
  fields,
  append,
  remove,
  readOnly = false
}) => {
  const weatherDataArrayError = Array.isArray(errors.weatherData) ? undefined : errors.weatherData?.message
  const weatherDataError = errors.weatherData?.root?.message ?? weatherDataArrayError

  return (
    <Grid size={12}>
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6">Weather Data</Typography>
            {!readOnly && (
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
            )}
          </Box>

          <TableContainer component={Paper}>
            <Table size="small" sx={{ minWidth: 850 }}>
              <TableHead>
                <TableRow>
                  <TableCell sx={dateCellSx}>Date/Time (PDT)</TableCell>
                  <TableCell sx={compactWeatherCellSx}>Temp (C)</TableCell>
                  <TableCell sx={compactWeatherCellSx}>RH (%)</TableCell>
                  <TableCell sx={windCellSx}>Wind</TableCell>
                  <TableCell sx={compactWeatherCellSx}>Rain (mm)</TableCell>
                  <TableCell sx={compactWeatherCellSx}>Chance Rain (%)</TableCell>
                  {!readOnly && <TableCell width={60} />}
                </TableRow>
              </TableHead>
              <TableBody>
                {fields.map((field, index) => (
                  <TableRow key={field.id}>
                    <WeatherDataCell
                      name={`weatherData.${index}.dateTime` as FieldPath<SpotFormData>}
                      control={control}
                      readOnly={readOnly}
                      errorMessage={errors.weatherData?.[index]?.dateTime?.message}
                      sx={dateCellSx}
                    />
                    <WeatherDataCell
                      name={`weatherData.${index}.temp` as FieldPath<SpotFormData>}
                      control={control}
                      type="number"
                      readOnly={readOnly}
                      errorMessage={errors.weatherData?.[index]?.temp?.message}
                      sx={compactWeatherCellSx}
                    />
                    <WeatherDataCell
                      name={`weatherData.${index}.rh` as FieldPath<SpotFormData>}
                      control={control}
                      type="number"
                      readOnly={readOnly}
                      errorMessage={errors.weatherData?.[index]?.rh?.message}
                      sx={compactWeatherCellSx}
                    />
                    <WeatherDataCell
                      name={`weatherData.${index}.wind` as FieldPath<SpotFormData>}
                      control={control}
                      readOnly={readOnly}
                      sx={windCellSx}
                    />
                    <WeatherDataCell
                      name={`weatherData.${index}.rain` as FieldPath<SpotFormData>}
                      control={control}
                      readOnly={readOnly}
                      sx={compactWeatherCellSx}
                    />
                    <WeatherDataCell
                      name={`weatherData.${index}.chanceRain` as FieldPath<SpotFormData>}
                      control={control}
                      readOnly={readOnly}
                      sx={compactWeatherCellSx}
                    />
                    {!readOnly && (
                      <TableCell>
                        <IconButton size="small" color="error" onClick={() => remove(index)}>
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </TableCell>
                    )}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          {weatherDataError && (
            <Typography color="error" sx={{ mt: 1 }}>
              {weatherDataError}
            </Typography>
          )}
        </CardContent>
      </Card>
    </Grid>
  )
}

export default WeatherDataTable
