import { TextField } from '@material-ui/core'
import { ClassNameMap } from '@material-ui/core/styles/withStyles'
import { FBAInputGridProps } from 'features/fbaCalculator/components/FBAInputGrid'
import { buildUpdatedNumberRow, updateFBARow } from 'features/fbaCalculator/tableState'
import { isGrassCureInvalid } from 'features/fbaCalculator/validation'
import { isEqual, isNull, isUndefined } from 'lodash'
import React, { ChangeEvent, useState } from 'react'

export interface GrassCureCellProps {
  fbaInputGridProps: Pick<FBAInputGridProps, 'inputRows' | 'updateRow'>
  classNameMap: ClassNameMap<'grassCure'>
  value: number | undefined
  rowId: number
}

const GrassCureProps = (props: GrassCureCellProps) => {
  const [lastRequestedGrassCure, setLastRequestedGrassCure] = useState(props.value)
  const [grassCurePercentage, setGrassCurePercentage] = useState(props.value)

  const changeHandler = (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const stringInput = String(event.target.value)
    const numberInput = parseInt(stringInput)
    if (
      isUndefined(stringInput) ||
      isNull(stringInput) ||
      isNaN(numberInput) ||
      stringInput.length <= 3
    ) {
      setGrassCurePercentage(parseInt(event.target.value))
    }
  }

  const handlePossibleUpdate = () => {
    if (!isEqual(lastRequestedGrassCure, grassCurePercentage)) {
      setLastRequestedGrassCure(grassCurePercentage)
      const updatedRow = buildUpdatedNumberRow(
        props.fbaInputGridProps.inputRows[props.rowId],
        'grassCure',
        grassCurePercentage
      )
      const dispatchRequest = !isGrassCureInvalid(updatedRow)
      updateFBARow(
        props.fbaInputGridProps,
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

  const hasError = isGrassCureInvalid(props.fbaInputGridProps.inputRows[props.rowId])

  return (
    <TextField
      data-testid={`grassCureInput-${props.rowId}`}
      type="number"
      inputMode="numeric"
      className={props.classNameMap.grassCure}
      size="small"
      variant="outlined"
      inputProps={{ min: 0, max: 100 }}
      onChange={changeHandler}
      onBlur={handlePossibleUpdate}
      onKeyDown={enterHandler}
      value={grassCurePercentage}
      error={hasError}
    />
  )
}

export default React.memo(GrassCureProps)
