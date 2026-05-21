import React from 'react'
import { SxProps, TableCell, Theme } from '@mui/material'
import { Control, FieldPath } from 'react-hook-form'
import { SpotFormData } from '@wps/api/schema/spotForecastSchema'
import ControlledForecastTextField from '@/features/smurfi/components/forecastForm/ControlledForecastTextField'

interface WeatherDataCellProps {
  control: Control<SpotFormData>
  name: FieldPath<SpotFormData>
  errorMessage?: string
  type?: 'text' | 'number'
  sx?: SxProps<Theme>
}

const WeatherDataCell: React.FC<WeatherDataCellProps> = ({ control, name, errorMessage, type = 'text', sx }) => (
  <TableCell sx={sx}>
    <ControlledForecastTextField
      name={name}
      control={control}
      type={type}
      size="small"
      fullWidth
      errorMessage={errorMessage}
    />
  </TableCell>
)

export default WeatherDataCell
