import { GridRenderEditCellParams, useGridApiContext } from '@mui/x-data-grid-pro'
import React, { useRef, useEffect } from 'react'
import { TextField } from '@mui/material'
import { theme } from '@/app/theme'
import { isEmpty } from 'lodash'
import { AppDispatch } from '@/app/store'
import { useDispatch } from 'react-redux'
import { setInputValid } from '@/features/moreCast2/slices/validInputSlice'
import InvalidCellToolTip from '@/features/moreCast2/components/InvalidCellToolTip'

export const EditInputCell = (props: GridRenderEditCellParams) => {
  const { id, value, field, hasFocus, error } = props
  const apiRef = useGridApiContext()
  const inputRef = useRef<HTMLInputElement | null>(null)
  const dispatch: AppDispatch = useDispatch()

  dispatch(setInputValid(isEmpty(error)))

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
      event.stopPropagation()
      if (isEmpty(error)) {
        apiRef.current.stopCellEditMode({ id, field })
      } else {
        event.stopPropagation()
      }
    }
  }

  return (
    <InvalidCellToolTip error={error}>
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
            },
            '&:hover fieldset': {
              borderColor: error ? theme.palette.error.main : '#737373'
            },
            '&.Mui-focused fieldset': {
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
    </InvalidCellToolTip>
  )
}
