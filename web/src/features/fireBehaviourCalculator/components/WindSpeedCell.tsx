import { TextField } from '@material-ui/core'
import { ClassNameMap } from '@material-ui/core/styles/withStyles'
import { FBCInputGridProps } from 'features/fireBehaviourCalculator/components/FBCInputGrid'
import {
  buildUpdatedNumberRow,
  updateFBCRow
} from 'features/fireBehaviourCalculator/tableState'
import React, { ChangeEvent } from 'react'

interface WindSpeedCellProps {
  fbcInputGridProps: Pick<FBCInputGridProps, 'stationOptions' | 'inputRows' | 'updateRow'>
  classNameMap: ClassNameMap<'windSpeed'>
  state: {
    windSpeedValue: number | undefined
    setWindSpeedValue: (newValue: number | undefined) => void
  }
  rowId: number
}
const WindSpeedCell = (props: WindSpeedCellProps) => {
  const changeHandler = (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    updateFBCRow(
      props.fbcInputGridProps,
      props.rowId,
      'windSpeed',
      parseInt(event.target.value),
      buildUpdatedNumberRow
    )
    props.state.setWindSpeedValue(parseInt(event.target.value))
  }

  return (
    <TextField
      type="number"
      className={props.classNameMap.windSpeed}
      size="small"
      variant="outlined"
      inputProps={{ min: 0, maxLength: 4, size: 4 }}
      onChange={changeHandler}
      value={props.state.windSpeedValue}
    />
  )
}

export default React.memo(WindSpeedCell)
