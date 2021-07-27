import { TextField } from '@material-ui/core'
import { ClassNameMap } from '@material-ui/core/styles/withStyles'
import { FBCInputGridProps } from 'features/fireBehaviourCalculator/components/FBCInputGrid'
import {
  buildUpdatedNumberRow,
  updateFBCRow
} from 'features/fireBehaviourCalculator/tableState'
import React, { ChangeEvent, useState } from 'react'
import { useEffect } from 'react'

interface WindSpeedCellProps {
  fbcInputGridProps: Pick<
    FBCInputGridProps,
    'stationOptions' | 'inputRows' | 'updateRow' | 'autoUpdateOnBlur'
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
    updateFBCRow(
      props.fbcInputGridProps,
      props.rowId,
      'windSpeed',
      parseInt(event.target.value),
      buildUpdatedNumberRow
    )
    setWindSpeedValue(parseInt(event.target.value))
  }

  return (
    <TextField
      type="number"
      className={props.classNameMap.windSpeed}
      size="small"
      variant="outlined"
      inputProps={{ min: 0, maxLength: 4, size: 4 }}
      onChange={changeHandler}
      onBlur={props.fbcInputGridProps.autoUpdateOnBlur}
      value={windSpeedValue}
    />
  )
}

export default React.memo(WindSpeedCell)
