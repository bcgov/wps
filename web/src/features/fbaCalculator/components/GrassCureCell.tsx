import { TextField } from '@material-ui/core'
import { ClassNameMap } from '@material-ui/core/styles/withStyles'
import {
  FBAInputGridProps,
  FBAInputRow
} from 'features/fbaCalculator/components/FBAInputGrid'
import { buildUpdatedNumberRow, updateFBARow } from 'features/fbaCalculator/tableState'
import { isUndefined, isNull } from 'lodash'
import React, { ChangeEvent, useState } from 'react'

interface GrassCureCellProps {
  fbaInputGridProps: Pick<
    FBAInputGridProps,
    'inputRows' | 'updateRow' | 'autoUpdateHandler'
  >
  classNameMap: ClassNameMap<'grassCure'>
  value: number | undefined
  rowId: number
}

const grassCureNotSetForGrassType = (row: FBAInputRow): boolean => {
  if (isUndefined(row)) {
    return false
  }
  if (row.fuelType === 'o1a' || row.fuelType === 'o1b') {
    return isUndefined(row.grassCure) || isNaN(row.grassCure)
  }
  if (!isUndefined(row.grassCure) && !isNull(row.grassCure)) {
    return row.grassCure > 100
  }
  return false
}
const GrassCureProps = (props: GrassCureCellProps) => {
  const [grassCurePercentage, setGrassCurePercentage] = useState(props.value)

  const changeHandler = (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setGrassCurePercentage(parseInt(event.target.value))
  }

  const blurHandler = () => {
    updateFBARow(
      props.fbaInputGridProps,
      props.rowId,
      'grassCure',
      grassCurePercentage,
      buildUpdatedNumberRow
    )
  }

  const hasError = grassCureNotSetForGrassType(
    props.fbaInputGridProps.inputRows[props.rowId]
  )

  return (
    <TextField
      type="number"
      className={props.classNameMap.grassCure}
      size="small"
      variant="outlined"
      inputProps={{ min: 0, maxLength: 4, size: 4, max: 100 }}
      onChange={changeHandler}
      onBlur={blurHandler}
      onKeyDown={event => {
        if (event.key === 'Enter') {
          event.preventDefault()
          props.fbaInputGridProps.autoUpdateHandler()
        }
      }}
      value={grassCurePercentage}
      error={hasError}
    />
  )
}

export default React.memo(GrassCureProps)
