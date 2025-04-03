import { TextField, Tooltip } from '@mui/material'
import { ThemeProvider } from '@mui/material/styles'
import { FBATableRow } from 'features/fbaCalculator/RowManager'
import { updateFBARow, buildUpdatedNumberRow } from 'features/fbaCalculator/tableState'
import { isPrecipInvalid } from 'features/fbaCalculator/validation'
import { isEqual, isUndefined } from 'lodash'
import React, { ChangeEvent, useState, useEffect } from 'react'
import { adjustedTheme } from 'features/fbaCalculator/components/WindSpeedCell'

export interface PrecipCellProps {
  inputRows: FBATableRow[]
  updateRow: (rowId: number, updatedRow: FBATableRow, dispatchRequest?: boolean) => void
  inputValue: number | undefined
  calculatedValue: number | undefined
  disabled: boolean
  rowId: number
}

const PrecipCell = (props: PrecipCellProps) => {
  const value = props.inputValue ?? props.calculatedValue
  const [precipValue, setPrecipValue] = useState(value)
  useEffect(() => {
    setPrecipValue(value)
  }, [value])

  const changeHandler = (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setPrecipValue(parseFloat(event.target.value))
  }

  const handlePossibleUpdate = () => {
    if (!isEqual(precipValue, props.calculatedValue)) {
      const dispatchRequest = !isPrecipInvalid(precipValue)
      updateFBARow(
        props.inputRows,
        props.updateRow,
        props.rowId,
        'precipitation',
        precipValue,
        buildUpdatedNumberRow,
        dispatchRequest
      )
    }
  }

  const enterHandler = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key === 'Enter') {
      handlePossibleUpdate()
    }
  }

  const hasError = isPrecipInvalid(precipValue)

  const valueForRendering = () => {
    if (precipValue === 0) {
      return 0
    }
    return isUndefined(precipValue) ? '' : precipValue
  }

  const buildTextField = () => (
    <Tooltip title="Cannot exceed 200" aria-label="cannot-exceed-200">
      <TextField
        data-testid={`precipInput-fba-${props.rowId}`}
        type="number"
        inputMode="numeric"
        size="small"
        variant="outlined"
        inputProps={{ min: 0, max: 200, step: '1' }}
        onChange={changeHandler}
        onBlur={handlePossibleUpdate}
        onKeyDown={enterHandler}
        value={valueForRendering()}
        disabled={props.disabled}
        error={hasError}
        sx={{ width: 80 }}
      />
    </Tooltip>
  )

  return props.inputValue && !hasError ? (
    <ThemeProvider theme={adjustedTheme}>{buildTextField()}</ThemeProvider>
  ) : (
    buildTextField()
  )
}

export default React.memo(PrecipCell)
