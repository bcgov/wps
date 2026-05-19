import React from 'react'
import { DateTimePicker } from '@mui/x-date-pickers'
import { Control, Controller } from 'react-hook-form'
import { SpotFormData } from '@wps/api/schema/spotForecastSchema'

interface ControlledForecastDateTimePickerProps {
  control: Control<SpotFormData>
  name: 'issuedDate' | 'expiryDate'
  label: string
  disabled?: boolean
  errorMessage?: string
}

const ControlledForecastDateTimePicker: React.FC<ControlledForecastDateTimePickerProps> = ({
  control,
  name,
  label,
  disabled = false,
  errorMessage
}) => (
  <Controller
    name={name}
    control={control}
    render={({ field }) => (
      <DateTimePicker
        label={label}
        value={field.value}
        onChange={field.onChange}
        timezone="America/Vancouver"
        disabled={disabled}
        slotProps={{
          textField: {
            fullWidth: true,
            error: !!errorMessage,
            helperText: errorMessage
          }
        }}
      />
    )}
  />
)

export default ControlledForecastDateTimePicker
