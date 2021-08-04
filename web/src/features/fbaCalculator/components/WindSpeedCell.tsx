import { TextField } from '@material-ui/core'
import { ClassNameMap } from '@material-ui/core/styles/withStyles'
import { FBAInputGridProps } from 'features/fbaCalculator/components/FBAInputGrid'
import { updateFBARow, buildUpdatedNumberRow } from 'features/fbaCalculator/tableState'
import { isEqual } from 'lodash'
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
    setWindSpeedValue(parseFloat(event.target.value))
  }

  const blurHandler = () => {
    if (!isEqual(windSpeedValue, props.calculatedValue)) {
      updateFBARow(
        props.fbaInputGridProps,
        props.rowId,
        'windSpeed',
        windSpeedValue,
        buildUpdatedNumberRow
      )
    }
  }

  return (
    <TextField
      data-testid={`windSpeedInput-${props.rowId}`}
      type="number"
      inputMode="numeric"
      className={props.classNameMap.windSpeed}
      size="small"
      variant="outlined"
      inputProps={{ min: 0, max: 100, step: 'any' }}
      onChange={changeHandler}
      onBlur={blurHandler}
      onKeyDown={event => {
        if (event.key === 'Enter') {
          updateFBARow(
            props.fbaInputGridProps,
            props.rowId,
            'windSpeed',
            windSpeedValue,
            buildUpdatedNumberRow
          )
        }
      }}
      value={windSpeedValue}
    />
  )
}

export default React.memo(WindSpeedCell)
