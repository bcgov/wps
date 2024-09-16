import React from 'react'
import { TextField } from '@mui/material'
import { GridRenderCellParams } from '@mui/x-data-grid-pro'
import { theme } from 'app/theme'

interface ValidatedForecastCellProps {
  disabled: boolean
  label: string
  value: Pick<GridRenderCellParams, 'formattedValue'>
  validator?: (value: string) => string
}

const ValidatedForecastCell = ({ disabled, label, value, validator }: ValidatedForecastCellProps) => {
  const error = validator ? validator(value as string) : ''
  return (
    <TextField
      data-testid="validated-forecast-cell"
      disabled={disabled}
      size="small"
      label={label}
      InputLabelProps={{
        shrink: true
      }}
      sx={{
        '& .MuiOutlinedInput-root': {
          backgroundColor: `${theme.palette.common.white}`,
          '& fieldset': {
            borderColor: error ? theme.palette.error.main : '#737373',
            borderWidth: '2px'
          },
          '&:hover fieldset': {
            borderColor: error ? theme.palette.error.main : '#737373'
          },
          '&.Mui-focused fieldset': {
            borderColor: error ? theme.palette.error.main : '#737373',
            borderWidth: '2px'
          }
        },
        '& .Mui-disabled': {
          '& fieldset': {
            borderWidth: '1px'
          }
        }
      }}
      value={value}
    ></TextField>
  )
}

export default React.memo(ValidatedForecastCell)
