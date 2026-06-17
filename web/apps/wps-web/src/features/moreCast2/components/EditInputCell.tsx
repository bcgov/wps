import { TextField } from '@mui/material'
import { type GridRenderEditCellParams, useGridApiContext } from '@mui/x-data-grid-pro'
import { theme } from '@wps/ui/theme'
import { isEmpty } from 'lodash'
import type React from 'react'
import { useEffect, useRef } from 'react'
import { useDispatch } from 'react-redux'
import type { AppDispatch } from '@/app/store'
import InvalidCellToolTip from '@/features/moreCast2/components/InvalidCellToolTip'
import { setInputValid } from '@/features/moreCast2/slices/validInputSlice'

export const EditInputCell = (props: GridRenderEditCellParams) => {
  const { id, value, field, hasFocus, error } = props
  const apiRef = useGridApiContext()
  const inputRef = useRef<HTMLInputElement | null>(null)
  const dispatch: AppDispatch = useDispatch()

  useEffect(() => {
    dispatch(setInputValid(isEmpty(error)))
  }, [dispatch])

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
    <InvalidCellToolTip invalid={error}>
      <TextField
        data-testid="forecast-edit-cell"
        type="number"
        inputMode="numeric"
        inputRef={inputRef}
        size="small"
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
        slotProps={{
          inputLabel: {
            shrink: true
          }
        }}
      />
    </InvalidCellToolTip>
  )
}
