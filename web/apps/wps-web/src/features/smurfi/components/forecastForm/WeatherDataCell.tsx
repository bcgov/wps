import React from 'react'
import { TableCell } from '@mui/material'
import { Control, FieldPath } from 'react-hook-form'
import { SpotFormData } from '@wps/api/schema/spotForecastSchema'
import ControlledForecastTextField from '@/features/smurfi/components/forecastForm/ControlledForecastTextField'

interface WeatherDataCellProps {
  control: Control<SpotFormData>
  name: FieldPath<SpotFormData>
  errorMessage?: string
  readOnly: boolean
  type?: 'text' | 'number'
}

const WeatherDataCell: React.FC<WeatherDataCellProps> = ({ control, name, errorMessage, readOnly, type = 'text' }) => (
  <TableCell>
    <ControlledForecastTextField
      name={name}
      control={control}
      type={type}
      size="small"
      fullWidth
      readOnly={readOnly}
      errorMessage={errorMessage}
    />
  </TableCell>
)

export default WeatherDataCell
