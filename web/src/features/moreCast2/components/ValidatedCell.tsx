import { theme } from '@/app/theme'
import InvalidCellToolTip from '@/features/moreCast2/components/InvalidCellToolTip'
import { TextField } from '@mui/material'
import { GridRenderCellParams } from '@mui/x-data-grid-pro'
import React from 'react'

interface ValidatedCellProps {
  disabled: boolean
  label: string
  error: boolean
  invalid: string
  value: Pick<GridRenderCellParams, 'formattedValue'>
}

const ValidatedGrassCureForecastCell = ({ disabled, label, value, invalid, error }: ValidatedCellProps) => {
  return (
    <InvalidCellToolTip invalid={invalid}>
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
    </InvalidCellToolTip>
  )
}

export default React.memo(ValidatedGrassCureForecastCell)
