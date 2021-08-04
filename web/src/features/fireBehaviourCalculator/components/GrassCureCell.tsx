import { TextField } from '@material-ui/core'
import { ClassNameMap } from '@material-ui/core/styles/withStyles'
import { FBCInputGridProps } from 'features/fireBehaviourCalculator/components/FBCInputGrid'
import {
  buildUpdatedNumberRow,
  updateFBCRow
} from 'features/fireBehaviourCalculator/tableState'
import { grassCureNotSetForGrassType } from 'features/fireBehaviourCalculator/utils'
import { isEqual } from 'lodash'
import React, { ChangeEvent, useState } from 'react'

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
  const [lastRequestedGrassCure, setLastRequestedGrassCure] = useState(props.value)
  const [grassCurePercentage, setGrassCurePercentage] = useState(props.value)

  const changeHandler = (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setGrassCurePercentage(parseInt(event.target.value))
  }

  const handlePossibleUpdate = () => {
    if (!isEqual(lastRequestedGrassCure, grassCurePercentage)) {
      setLastRequestedGrassCure(grassCurePercentage)
      const updatedRow = buildUpdatedNumberRow(
        props.fbcInputGridProps.inputRows[props.rowId],
        'grassCure',
        grassCurePercentage
      )
      const dispatchRequest = !grassCureNotSetForGrassType(updatedRow)
      updateFBCRow(
        props.fbcInputGridProps,
        props.rowId,
        'grassCure',
        grassCurePercentage,
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
      onBlur={handlePossibleUpdate}
      onKeyDown={enterHandler}
      value={grassCurePercentage}
      error={hasError}
    />
  )
}

export default React.memo(GrassCureProps)
