import { GridRenderEditCellParams, useGridApiContext } from '@mui/x-data-grid-pro'
import { styled } from '@mui/material/styles'
import Tooltip, { tooltipClasses, TooltipProps } from '@mui/material/Tooltip'
import React, { useRef, useEffect } from 'react'
import { TextField } from '@mui/material'
import { theme } from '@/app/theme'

const StyledTooltip = styled(({ className, ...props }: TooltipProps) => (
  <Tooltip {...props} classes={{ popper: className }} />
))(({ theme }) => ({
  [`& .${tooltipClasses.tooltip}`]: {
    backgroundColor: theme.palette.error.main,
    color: theme.palette.error.contrastText
  }
}))

export const EditInputCell = (props: GridRenderEditCellParams) => {
  const { id, value, field, hasFocus, error } = props
  const apiRef = useGridApiContext()
  const inputRef = useRef<HTMLInputElement | null>(null)

  useEffect(() => {
    if (hasFocus && inputRef.current) {
      inputRef.current.focus()
    }
  }, [hasFocus])

  const handleValueChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = event.target.value
    apiRef.current.setEditCellValue({ id, field, value: newValue })
  }

  const handleBlur = () => {
    apiRef.current.stopCellEditMode({ id, field })
  }

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Escape') {
      apiRef.current.stopCellEditMode({ id, field })
    }
  }

  return (
    <StyledTooltip open={!!error} title={error}>
      <TextField
        data-testid="forecast-edit-cell"
        type="number"
        inputMode="numeric"
        inputRef={inputRef}
        size="small"
        InputLabelProps={{
          shrink: true
        }}
        sx={{
          '& .MuiOutlinedInput-root': {
            '& fieldset': {
              borderColor: error ? theme.palette.error.main : '#737373',
              borderWidth: '2px'
            }
          }
        }}
        value={value}
        onChange={handleValueChange}
        onBlur={handleBlur}
        onKeyDown={handleKeyDown}
      />
    </StyledTooltip>
  )
}
