import { TextField, Tooltip, adaptV4Theme } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import {
  createTheme,
  ThemeProvider,
  Theme,
  StyledEngineProvider
} from '@mui/material/styles'
import { FBATableRow } from 'features/fbaCalculator/RowManager'
import { updateFBARow, buildUpdatedNumberRow } from 'features/fbaCalculator/tableState'
import { isWindSpeedInvalid } from 'features/fbaCalculator/validation'
import { isEqual, isUndefined } from 'lodash'
import React, { ChangeEvent, useState, useEffect } from 'react'

declare module '@mui/styles/defaultTheme' {
  // eslint-disable-next-line @typescript-eslint/no-empty-interface
  interface DefaultTheme extends Theme {}
}

export interface WindSpeedCellProps {
  inputRows: FBATableRow[]
  updateRow: (rowId: number, updatedRow: FBATableRow, dispatchRequest?: boolean) => void
  inputValue: number | undefined
  calculatedValue: number | undefined
  disabled: boolean
  rowId: number
}

const useStyles = makeStyles({
  windSpeed: {
    width: 80
  }
})

const adjustedTheme = createTheme(
  adaptV4Theme({
    overrides: {
      MuiInputBase: {
        root: {
          border: '2px solid #460270'
        }
      }
    }
  })
)

const WindSpeedCell = (props: WindSpeedCellProps) => {
  const classes = useStyles()
  const value = props.inputValue ? props.inputValue : props.calculatedValue
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

  const valueForRendering = () => {
    if (windSpeedValue === 0) {
      return 0
    }
    return isUndefined(windSpeedValue) ? '' : windSpeedValue
  }

  const buildTextField = () => (
    <Tooltip title="Cannot exceed 120" aria-label="cannot-exceed-120">
      <TextField
        data-testid={`windSpeedInput-fba-${props.rowId}`}
        type="number"
        inputMode="numeric"
        className={classes.windSpeed}
        size="small"
        variant="outlined"
        inputProps={{ min: 0, max: 120, step: 'any' }}
        onChange={changeHandler}
        onBlur={handlePossibleUpdate}
        onKeyDown={enterHandler}
        value={valueForRendering()}
        disabled={props.disabled}
        error={hasError}
      />
    </Tooltip>
  )

  return props.inputValue && !hasError ? (
    <StyledEngineProvider injectFirst>
      <ThemeProvider theme={adjustedTheme}>{buildTextField()}</ThemeProvider>
    </StyledEngineProvider>
  ) : (
    buildTextField()
  )
}

export default React.memo(WindSpeedCell)
