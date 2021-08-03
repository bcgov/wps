import { TextField } from '@material-ui/core'
import { ClassNameMap } from '@material-ui/core/styles/withStyles'
import { FBAInputGridProps } from 'features/fbaCalculator/components/FBAInputGrid'
import { buildUpdatedNumberRow, updateFBARow } from 'features/fbaCalculator/tableState'
import React, { ChangeEvent, useState } from 'react'
import { useEffect } from 'react'

interface WindSpeedCellProps {
  fbaInputGridProps: Pick<
    FBAInputGridProps,
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
    setWindSpeedValue(parseInt(event.target.value))
  }

  const blurHandler = () => {
    updateFBARow(
      props.fbaInputGridProps,
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
      inputProps={{ min: 0, maxLength: 4, size: 4 }}
      onChange={changeHandler}
      onBlur={blurHandler}
      onKeyDown={event => {
        if (event.key === 'Enter') {
          event.preventDefault()
          props.fbaInputGridProps.autoUpdateHandler()
        }
      }}
      value={windSpeedValue}
    />
  )
}

export default React.memo(WindSpeedCell)
