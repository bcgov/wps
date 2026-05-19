import React from 'react'
import { TextField, TextFieldProps } from '@mui/material'
import { Control, Controller, FieldPath } from 'react-hook-form'
import { SpotFormData } from '@wps/api/schema/spotForecastSchema'

interface ControlledForecastTextFieldProps extends Omit<
  TextFieldProps,
  'error' | 'helperText' | 'name' | 'onChange' | 'value'
> {
  control: Control<SpotFormData>
  name: FieldPath<SpotFormData>
  errorMessage?: string
  readOnly?: boolean
  endAdornment?: React.ReactNode
  parseValue?: (value: string) => unknown
}

const ControlledForecastTextField: React.FC<ControlledForecastTextFieldProps> = ({
  control,
  name,
  errorMessage,
  readOnly = false,
  endAdornment,
  parseValue,
  ...textFieldProps
}) => (
  <Controller
    name={name}
    control={control}
    render={({ field }) => (
      <TextField
        {...field}
        {...textFieldProps}
        value={field.value ?? ''}
        error={!!errorMessage}
        helperText={errorMessage}
        onChange={event => field.onChange(parseValue ? parseValue(event.target.value) : event.target.value)}
        slotProps={{
          input: {
            readOnly,
            endAdornment
          }
        }}
      />
    )}
  />
)

export default ControlledForecastTextField
