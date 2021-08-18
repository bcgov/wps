import { TextField, Tooltip, makeStyles } from '@material-ui/core'
import { createMuiTheme, ThemeProvider } from '@material-ui/core/styles'
import { FBCTableRow } from 'features/fbaCalculator/RowManager'
import { updateFBARow, buildUpdatedNumberRow } from 'features/fbaCalculator/tableState'
import { isWindSpeedInvalid } from 'features/fbaCalculator/validation'
import { isEqual } from 'lodash'
import React, { ChangeEvent, useState, useEffect } from 'react'

export interface WindSpeedCellProps {
  inputRows: FBCTableRow[]
  updateRow: (rowId: number, updatedRow: FBCTableRow, dispatchRequest?: boolean) => void
  inputValue: number | undefined
  calculatedValue: number | undefined
  rowId: number
}

const useStyles = makeStyles({
  windSpeed: {
    width: 80
  }
})

const adjustedTheme = createMuiTheme({
  overrides: {
    MuiInputBase: {
      root: {
        border: '2px solid #460270'
      }
    }
  }
})

const WindSpeedCell = (props: WindSpeedCellProps) => {
  const classes = useStyles()
  const value = props.calculatedValue ? props.calculatedValue : props.inputValue
  const [windSpeedValue, setWindSpeedValue] = useState(value)
  useEffect(() => {
    setWindSpeedValue(value)
  }, [value])

  const changeHandler = (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setWindSpeedValue(parseFloat(event.target.value))
  }

  const handlePossibleUpdate = () => {
    if (!isEqual(windSpeedValue, props.calculatedValue)) {
      const dispatchRequest = !isWindSpeedInvalid(windSpeedValue)
      updateFBARow(
        props.inputRows,
        props.updateRow,
        props.rowId,
        'windSpeed',
        windSpeedValue,
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

  const hasError = isWindSpeedInvalid(windSpeedValue)

  const buildTextField = () => (
    <Tooltip title="Cannot exceed 120" aria-label="cannot-exceed-120">
      <TextField
        data-testid={`windSpeedInput-${props.rowId}`}
        type="number"
        inputMode="numeric"
        className={classes.windSpeed}
        size="small"
        variant="outlined"
        inputProps={{ min: 0, max: 120, step: 'any' }}
        onChange={changeHandler}
        onBlur={handlePossibleUpdate}
        onKeyDown={enterHandler}
        value={windSpeedValue}
        error={hasError}
      />
    </Tooltip>
  )

  return props.inputValue && !hasError ? (
    <ThemeProvider theme={adjustedTheme}>{buildTextField()}</ThemeProvider>
  ) : (
    buildTextField()
  )
}

export default React.memo(WindSpeedCell)
