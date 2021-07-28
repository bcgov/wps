import { TextField } from '@material-ui/core'
import { ClassNameMap } from '@material-ui/core/styles/withStyles'
import {
  FBCInputGridProps,
  FBCInputRow
} from 'features/fireBehaviourCalculator/components/FBCInputGrid'
import {
  buildUpdatedNumberRow,
  updateFBCRow
} from 'features/fireBehaviourCalculator/tableState'
import { isUndefined, isNull } from 'lodash'
import React, { ChangeEvent } from 'react'

interface GrassCureCellProps {
  fbcInputGridProps: Pick<
    FBCInputGridProps,
    'inputRows' | 'updateRow' | 'autoUpdateHandler'
  >
  classNameMap: ClassNameMap<'grassCure'>
  value: number | undefined
  rowId: number
}

const grassCureNotSetForGrassType = (row: FBCInputRow): boolean => {
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
  const changeHandler = (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    updateFBCRow(
      props.fbcInputGridProps,
      props.rowId,
      'grassCure',
      parseInt(event.target.value),
      buildUpdatedNumberRow
    )
  }

  const hasError = grassCureNotSetForGrassType(
    props.fbcInputGridProps.inputRows[props.rowId]
  )

  return (
    <TextField
      type="number"
      className={props.classNameMap.grassCure}
      size="small"
      variant="outlined"
      inputProps={{ min: 0, maxLength: 4, size: 4, max: 100 }}
      onChange={changeHandler}
      onBlur={props.fbcInputGridProps.autoUpdateHandler}
      onKeyDown={event => {
        if (event.key === 'Enter') {
          event.preventDefault()
          props.fbcInputGridProps.autoUpdateHandler()
        }
      }}
      value={props.value}
      error={hasError}
    />
  )
}

export default React.memo(GrassCureProps)
