import React from 'react'
import { Controller, Control, UseFieldArrayReturn, FieldErrors } from 'react-hook-form'
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
  Box
} from '@mui/material'
import { DateTime } from 'luxon'
import AddIcon from '@mui/icons-material/Add'
import DeleteIcon from '@mui/icons-material/Delete'
import { FormData } from '@/features/smurfi/schemas/spotForecastSchema'

interface WeatherDataTableProps {
  control: Control<FormData>
  errors: FieldErrors<FormData>
  fields: UseFieldArrayReturn<FormData, 'weatherData'>['fields']
  append: UseFieldArrayReturn<FormData, 'weatherData'>['append']
  remove: UseFieldArrayReturn<FormData, 'weatherData'>['remove']
}

const WeatherDataTable: React.FC<WeatherDataTableProps> = ({ control, errors, fields, append, remove }) => {
  return (
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
                  <TableCell sx={{ minWidth: 175 }}>Date/Time (PDT)</TableCell>
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
  )
}

export default WeatherDataTable
