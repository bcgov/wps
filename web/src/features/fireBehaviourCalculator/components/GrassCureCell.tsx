import { TextField } from '@material-ui/core'
import { ClassNameMap } from '@material-ui/core/styles/withStyles'
import { FBCInputGridProps } from 'features/fireBehaviourCalculator/components/FBCInputGrid'
import {
  buildUpdatedNumberRow,
  updateFBCRow
} from 'features/fireBehaviourCalculator/tableState'
import { grassCureNotSetForGrassType } from 'features/fireBehaviourCalculator/validation'
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
