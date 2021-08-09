import { TextField, Tooltip } from '@material-ui/core'
import { ClassNameMap } from '@material-ui/core/styles/withStyles'
import { FBAInputGridProps } from 'features/fbaCalculator/components/FBAInputGrid'
import { updateFBARow, buildUpdatedNumberRow } from 'features/fbaCalculator/tableState'
import { isWindSpeedInvalid } from 'features/fbaCalculator/validation'
import { isEqual, isNull, isUndefined } from 'lodash'
import React, { ChangeEvent, useState, useEffect } from 'react'

export interface WindSpeedCellProps {
  fbaInputGridProps: Pick<FBAInputGridProps, 'stationOptions' | 'inputRows' | 'updateRow'>
  classNameMap: ClassNameMap<'windSpeed'>
  inputValue: number | undefined
  calculatedValue: number | undefined
  rowId: number
}
const WindSpeedCell = (props: WindSpeedCellProps) => {
  const value = props.calculatedValue ? props.calculatedValue : props.inputValue
  const [windSpeedValue, setWindSpeedValue] = useState(value)
  useEffect(() => {
    setWindSpeedValue(value)
  }, [value])

  const changeHandler = (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const stringInput = String(event.target.value)
    const numberInput = parseFloat(stringInput)
    if (
      isUndefined(stringInput) ||
      isNull(stringInput) ||
      isNaN(numberInput) ||
      stringInput.split('.')[0].length <= 3
    ) {
      setWindSpeedValue(parseFloat(event.target.value))
    }
  }

  const handlePossibleUpdate = () => {
    if (!isEqual(windSpeedValue, props.calculatedValue)) {
      const dispatchRequest = !isWindSpeedInvalid(windSpeedValue)
      updateFBARow(
        props.fbaInputGridProps,
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

  return (
    <Tooltip title="Cannot exceed 120" aria-label="cannot-exceed-120">
      <TextField
        data-testid={`windSpeedInput-${props.rowId}`}
        type="number"
        inputMode="numeric"
        className={props.classNameMap.windSpeed}
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
}

export default React.memo(WindSpeedCell)
