import { TextField } from '@material-ui/core'
import { ClassNameMap } from '@material-ui/core/styles/withStyles'
import {
  FBAInputGridProps,
  FBAInputRow
} from 'features/fbaCalculator/components/FBAInputGrid'
import { buildUpdatedNumberRow, updateFBARow } from 'features/fbaCalculator/tableState'
import { isUndefined, isNull, isEqual } from 'lodash'
import React, { ChangeEvent, useState } from 'react'

export interface GrassCureCellProps {
  fbaInputGridProps: Pick<FBAInputGridProps, 'inputRows' | 'updateRow'>
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
  const [lastRequestedGrassCure, setLastRequestedGrassCure] = useState(props.value)
  const [grassCurePercentage, setGrassCurePercentage] = useState(props.value)

  const changeHandler = (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setGrassCurePercentage(parseInt(event.target.value))
  }

  const handlePossibleUpdate = () => {
    if (!isEqual(lastRequestedGrassCure, grassCurePercentage)) {
      setLastRequestedGrassCure(grassCurePercentage)
      updateFBARow(
        props.fbaInputGridProps,
        props.rowId,
        'grassCure',
        grassCurePercentage,
        buildUpdatedNumberRow
      )
    }
  }

  const enterHandler = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key === 'Enter') {
      handlePossibleUpdate()
    }
  }

  const hasError = grassCureNotSetForGrassType(
    props.fbaInputGridProps.inputRows[props.rowId]
  )

  return (
    <TextField
      data-testid={`grassCureInput-${props.rowId}`}
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
