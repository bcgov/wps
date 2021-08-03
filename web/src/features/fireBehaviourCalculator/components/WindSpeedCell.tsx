import { TextField } from '@material-ui/core'
import { ClassNameMap } from '@material-ui/core/styles/withStyles'
import { FBCInputGridProps } from 'features/fireBehaviourCalculator/components/FBCInputGrid'
import {
  buildUpdatedNumberRow,
  updateFBCRow
} from 'features/fireBehaviourCalculator/tableState'
import React, { ChangeEvent, useState, useEffect } from 'react'

interface WindSpeedCellProps {
  fbcInputGridProps: Pick<
    FBCInputGridProps,
    'stationOptions' | 'inputRows' | 'updateRow' | 'autoUpdateHandler'
  >
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
    updateFBCRow(
      props.fbcInputGridProps,
      props.rowId,
      'windSpeed',
      windSpeedValue,
      buildUpdatedNumberRow
    )
  }

  return (
    <TextField
      type="number"
      className={props.classNameMap.windSpeed}
      size="small"
      variant="outlined"
      inputProps={{ min: 0, max: 100 }}
      onChange={changeHandler}
      onBlur={blurHandler}
      onKeyDown={event => {
        if (event.key === 'Enter') {
          event.preventDefault()
          props.fbcInputGridProps.autoUpdateHandler()
        }
      }}
      value={windSpeedValue}
    />
  )
}

export default React.memo(WindSpeedCell)
